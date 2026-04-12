"""Submission baseline inference script.

Required env vars:
- API_BASE_URL: OpenAI-compatible model endpoint
- MODEL_NAME: model identifier
- HF_TOKEN: token required by submission infra
- OPENAI_API_KEY: key used by OpenAI client

Optional env vars:
- ENV_BASE_URL: environment server URL (default: http://localhost:8000)
"""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    from openai import OpenAI

try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # type: ignore[assignment,misc]

try:
    from email_triage_env.client import EmailTriageEnv
except Exception:
    EmailTriageEnv = None  # type: ignore[assignment,misc]

BENCHMARK = "email_triage_env_v2"
MAX_STEPS_PER_TASK = 5
MAX_TOTAL_REWARD_PER_TASK = float(MAX_STEPS_PER_TASK)

TASKS: List[Dict[str, Any]] = [
    {
        "task": "email_triage_easy_v1",
        "difficulty": "easy",
        "seed": 101,
        "partial_info": False,
        "episode_length": 5,
    },
    {
        "task": "email_triage_medium_v1",
        "difficulty": "medium",
        "seed": 202,
        "partial_info": True,
        "episode_length": 5,
    },
    {
        "task": "email_triage_hard_v1",
        "difficulty": "hard",
        "seed": 303,
        "partial_info": True,
        "episode_length": 5,
    },
]


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def env_or_default(name: str, default: str) -> str:
    value = os.getenv(name, "").strip()
    return value if value else default


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: Dict[str, Any], reward: float, done: bool, error: str | None) -> None:
    action_text = json.dumps(action, separators=(",", ":"), sort_keys=True)
    err_text = "none" if error is None else error.replace("\n", " ")
    print(
        f"[STEP] step={step} action={action_text} reward={reward:.4f} done={str(done).lower()} error={err_text}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_text = json.dumps([round(r, 4) for r in rewards], separators=(",", ":"))
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.4f} rewards={rewards_text}",
        flush=True,
    )


def heuristic_action(email: Dict[str, Any]) -> Dict[str, Any]:
    subject = (email.get("subject") or "").lower()
    body = (email.get("body") or "").lower()
    text = f"{subject} {body}"

    spam_keywords = ["won", "click here", "free", "prize", "verify identity", "deleted", "cheap meds"]
    if any(k in text for k in spam_keywords):
        return {
            "is_spam": True,
            "category": "general",
            "priority": "low",
            "department": "none",
            "response_template": "spam_discard",
        }

    if any(k in text for k in ["invoice", "statement", "charge", "payment", "renewal", "contract"]):
        return {
            "is_spam": False,
            "category": "billing",
            "priority": "urgent" if "urgent" in text or "deadline" in text else "normal",
            "department": "finance" if "contract" not in text else "legal",
            "response_template": "contract_escalation" if "contract" in text else "billing_info",
        }

    if any(k in text for k in ["login", "password", "account suspended", "support"]):
        return {
            "is_spam": False,
            "category": "support",
            "priority": "urgent" if "urgent" in text else "normal",
            "department": "customer_support",
            "response_template": "password_reset_guide",
        }

    if any(k in text for k in ["pricing", "demo", "enterprise", "upgrade", "seats"]):
        return {
            "is_spam": False,
            "category": "sales",
            "priority": "urgent" if "urgent" in text or "expires" in text else "normal",
            "department": "sales",
            "response_template": "enterprise_demo_request",
        }

    if any(k in text for k in ["hr", "vacation", "interview", "onboarding", "policy"]):
        return {
            "is_spam": False,
            "category": "hr",
            "priority": "normal",
            "department": "human_resources",
            "response_template": "hr_policy_info",
        }

    return {
        "is_spam": False,
        "category": "general",
        "priority": "normal",
        "department": "customer_support",
        "response_template": "no_reply_needed",
    }


def get_model_action(client: Any, model: str, email: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
    prompt = {
        "instruction": "Classify this email into the exact output schema.",
        "schema": {
            "is_spam": "boolean",
            "category": options["categories"],
            "priority": options["priorities"],
            "department": options["departments"],
            "response_template": options["response_templates"],
        },
        "email": {
            "subject": email.get("subject", ""),
            "sender": email.get("sender", ""),
            "body": email.get("body", ""),
        },
        "output": "Return JSON only.",
    }

    if client is None:
        return heuristic_action(email)

    try:
        completion = client.chat.completions.create(
            model=model,
            temperature=0,
            messages=[
                {"role": "system", "content": "You are an email triage classifier."},
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=True)},
            ],
        )
        text = (completion.choices[0].message.content or "").strip()
        parsed = json.loads(text)

        return {
            "is_spam": bool(parsed.get("is_spam", False)),
            "category": str(parsed.get("category", "general")),
            "priority": str(parsed.get("priority", "normal")),
            "department": str(parsed.get("department", "customer_support")),
            "response_template": str(parsed.get("response_template", "no_reply_needed")),
        }
    except Exception:
        return heuristic_action(email)


def run_task(client: Any, model_name: str, env: Any, task: Dict[str, Any]) -> float:
    task_name = task["task"]
    rewards: List[float] = []
    steps_taken = 0

    log_start(task=task_name, env=BENCHMARK, model=model_name)

    env.reset(
        episode_length=task["episode_length"],
        difficulty=task["difficulty"],
        partial_info=task["partial_info"],
        seed=task["seed"],
    )
    options = env.get_available_options()["options"]

    done = False
    for step in range(1, MAX_STEPS_PER_TASK + 1):
        if done:
            break

        current = env.get_current_email()["email"]
        if task["partial_info"] and current.get("body_hidden"):
            env.call_tool("reveal_body")
            current = env.get_current_email()["email"]

        action = get_model_action(client, model_name, current, options)

        try:
            result = env.step(**action)
            reward_value = float(result["reward"]["reward"])
            done = bool(result["done"])
            error = None
        except Exception as exc:
            reward_value = 0.0
            done = True
            error = str(exc)

        rewards.append(reward_value)
        steps_taken = step
        log_step(step=step, action=action, reward=reward_value, done=done, error=error)

    score = sum(rewards) / MAX_TOTAL_REWARD_PER_TASK
    score = max(0.0, min(1.0, score))
    success = score >= 0.7

    log_end(success=success, steps=steps_taken, score=score, rewards=rewards)
    return round(score, 4)


def main() -> None:
    api_base_url = env_or_default("API_BASE_URL", "https://api.openai.com/v1")
    model_name = env_or_default("MODEL_NAME", "gpt-4o-mini")
    _ = os.getenv("HF_TOKEN", "").strip()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    env_base = os.getenv("ENV_BASE_URL", "http://localhost:8000")

    client: Any = None
    if OpenAI is None:
        print("[WARN] OpenAI package unavailable. Falling back to heuristic policy.", flush=True)
    elif api_key:
        try:
            client = OpenAI(base_url=api_base_url, api_key=api_key, timeout=5.0, max_retries=2)
        except Exception as e:
            print(f"[WARN] Failed to initialize OpenAI client: {e}", flush=True)
            print("[WARN] Falling back to heuristic policy.", flush=True)
    else:
        print("[WARN] OPENAI_API_KEY not set. Falling back to heuristic policy.", flush=True)

    if EmailTriageEnv is None:
        print("[WARN] EmailTriageEnv client unavailable. Ensure dependencies are installed.", flush=True)
        return

    task_scores: List[float] = []
    try:
        with EmailTriageEnv(base_url=env_base) as env:
            for task in TASKS:
                try:
                    task_scores.append(run_task(client, model_name, env, task))
                except Exception as e:
                    print(f"Error running task {task['task']}: {e}", flush=True)
                    task_scores.append(0.0)

        _ = sum(task_scores) / len(task_scores) if task_scores else 0.0
    except Exception as e:
        print(f"[WARN] Failed to connect to environment at {env_base}: {e}", flush=True)
        print("[WARN] Ensure your env server is running and reachable on ENV_BASE_URL.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[WARN] Unexpected runtime error: {e}", flush=True)
        import traceback

        traceback.print_exc()
        print("[WARN] Exiting gracefully to avoid unhandled-exception submission failures.", flush=True)
