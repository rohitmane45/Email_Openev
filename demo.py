"""
Email Triage Environment -- Demo Script v2
==========================================
Demonstrates all features:
  - Easy / Medium / Hard difficulty levels
  - Partial information mode (reveal_body tool)
  - Live leaderboard
  - Smart rule-based agent

Usage:
    python demo.py                        # default: runs all 3 difficulty modes
    python demo.py --mode easy            # only easy
    python demo.py --mode hard --partial  # hard + partial info
    python demo.py --url http://localhost:8000
"""

import argparse
import json
import sys
import time

RESET   = "\033[0m"
BOLD    = "\033[1m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
RED     = "\033[91m"
CYAN    = "\033[96m"
MAGENTA = "\033[95m"
BLUE    = "\033[94m"
WHITE   = "\033[97m"


def c(text, col):
    return f"{col}{text}{RESET}"


def header(title, width=62):
    line = "=" * width
    print("\n" + c(line, CYAN))
    print(c(f"  {title}", BOLD + CYAN))
    print(c(line, CYAN))


def subheader(title, width=62):
    line = "-" * width
    print("\n" + c(line, MAGENTA))
    print(c(f"  {title}", BOLD + MAGENTA))
    print(c(line, MAGENTA))


# ---- Smart agent ----------------------------------------------------------

def agent_decide(subject, sender, body):
    """Rule-based agent. Works in both full-info and partial-info modes."""
    text = f"{subject} {sender} {body}".lower()

    spam_signals = [
        "click here", "you've won", "cheap", "free viagra", "!!!",
        "prize", "spambase", "totallylegit", "verify your identity",
        "permanently deleted", "redelivery fee", "fast-courier",
        "company-helpdesk.net", "company-announcements.io",
    ]
    if any(s in text for s in spam_signals):
        return {
            "is_spam": True, "category": "general", "priority": "low",
            "department": "none", "response_template": "spam_discard",
        }

    if any(k in text for k in ["invoice", "overdue", "payment", "contract", "renewal", "billing", "statement", "charge", "end of quarter", "q1"]):
        dept = "legal" if ("contract" in text or "renewal" in text) else "finance"
        tmpl = "billing_escalation" if ("overdue" in text or "urgent" in text or "today" in text or "q1" in text) else "billing_info"
        priority = "urgent" if ("urgent" in text or "today" in text or "immediately" in text or "tomorrow" in text or "5 pm" in text) else "normal"
        return {
            "is_spam": False, "category": "billing", "priority": priority,
            "department": dept, "response_template": tmpl,
        }

    if any(k in text for k in ["login", "password", "cannot login", "account", "otp", "reset", "integration", "broken", "downtime", "sla breach"]):
        priority = "urgent" if any(k in text for k in ["urgent", "hour", "immediately", "losing", "production", "3 days"]) else "normal"
        tmpl = "billing_escalation" if ("sla" in text or "legal" in text or "downtime" in text) else "password_reset_guide"
        return {
            "is_spam": False, "category": "support", "priority": priority,
            "department": "customer_support", "response_template": tmpl,
        }

    if any(k in text for k in ["pricing", "enterprise", "seats", "demo", "procurement", "license", "upgrade", "premium tier", "following up", "sales"]):
        priority = "urgent" if ("expires" in text or "10 days" in text or "urgency" in text) else "normal"
        return {
            "is_spam": False, "category": "sales", "priority": priority,
            "department": "sales", "response_template": "enterprise_demo_request",
        }

    if any(k in text for k in ["vacation", "hr", "interview", "hiring", "candidate", "leave", "policy", "offsite", "onboarding", "performance review", "promotion"]):
        priority = "urgent" if ("emergency" in text or "friday" in text or "this week" in text or "48 hours" in text) else "normal"
        tmpl = "interview_scheduling" if "interview" in text else "hr_policy_info"
        return {
            "is_spam": False, "category": "hr", "priority": priority,
            "department": "human_resources", "response_template": tmpl,
        }

    return {
        "is_spam": False, "category": "general", "priority": "low",
        "department": "none", "response_template": "no_reply_needed",
    }


# ---- Episode runner -------------------------------------------------------

def run_episode(env, difficulty, partial_info, seed, episode_num):
    subheader(f"Episode {episode_num} | Difficulty: {difficulty.upper()} | Partial Info: {partial_info}")
    obs = env.reset(episode_length=5, difficulty=difficulty, partial_info=partial_info, seed=seed)
    ep_state = obs.get("state", {})
    print(c(f"  Episode ID : {ep_state.get('episode_id','N/A')}", CYAN))

    done = False
    while not done:
        # Get current email
        resp = env.get_current_email()
        email = resp.get("email", {})
        remaining = resp.get("emails_remaining", "?")

        print(c(f"\n  Remaining: {remaining}    ID: {email.get('id','?')}", YELLOW))
        print(c(f"  From   : {email.get('sender','?')}", BLUE))
        print(c(f"  Subject: {email.get('subject','?')}", BOLD + BLUE))

        subject = email.get("subject", "")
        sender  = email.get("sender", "")
        body    = email.get("body", "")

        # Partial info mode: agent decides whether to reveal body
        if partial_info and email.get("body_hidden"):
            # Smart strategy: reveal body only if subject is ambiguous
            ambiguous_signals = ["re:", "fwd:", "following up", "quick question", "update", "few items"]
            should_reveal = any(s in subject.lower() for s in ambiguous_signals)

            if should_reveal:
                reveal_resp = env.call_tool("reveal_body")
                body = reveal_resp.get("body", "")
                penalty = reveal_resp.get("penalty", 0)
                print(c(f"  [PARTIAL] Revealed body (penalty: -{penalty})", MAGENTA))
            else:
                print(c(f"  [PARTIAL] Decided to classify WITHOUT reading body", YELLOW))

        # Agent decision
        decision = agent_decide(subject, sender, body)
        print(c(f"  Decision : {json.dumps(decision)}", WHITE))

        # Wait 3 seconds so you can watch the dashboard update!
        time.sleep(3.0)

        # Submit
        result = env.classify_email(**decision)
        reward = result.get("reward", 0)
        total  = result.get("total_reward", 0)
        done   = result.get("done", True)

        reward_col = GREEN if reward >= 0.7 else (YELLOW if reward >= 0.4 else RED)
        print(c(f"  Reward   : {reward:.4f}  |  Total: {total:.4f}", reward_col))

        bd = result.get("field_breakdown", {})
        correct_count = sum(1 for v in bd.values() if v)
        tick_str = "  Fields  : " + " ".join(
            c("[OK]", GREEN) if bd.get(f) else c("[X]", RED)
            for f in ["is_spam", "category", "priority", "department", "response_template"]
        )
        print(tick_str)

    # Episode complete
    stats = env.call_tool("get_episode_statistics")
    ep_reward = stats["state"]["total_reward"]
    ep_avg    = stats["state"]["average_reward"]
    acc       = stats.get("field_accuracy", {})

    grade = "A" if ep_avg >= 0.8 else ("B" if ep_avg >= 0.6 else ("C" if ep_avg >= 0.4 else "D"))
    grade_col = GREEN if grade in ("A", "B") else RED

    print(c(f"\n  --- Episode Complete ---", BOLD + CYAN))
    print(c(f"  Total: {ep_reward:.4f}  Avg: {ep_avg:.4f}  Grade: {grade}", grade_col))

    return ep_reward, ep_avg


# ---- Main -----------------------------------------------------------------

def run_demo(base_url, mode, use_partial, seed):
    try:
        from email_triage_env import EmailTriageEnv
    except ImportError:
        print(c("ERROR: Could not import EmailTriageEnv.", RED))
        sys.exit(1)

    header("Email Triage Environment v2 -- Demo")
    print(f"  Server : {c(base_url, CYAN)}")

    with EmailTriageEnv(base_url=base_url) as env:
        # ---------- Health ----------
        try:
            h = env.health()
            print(c(f"  Server version: {h.get('version','?')}  Status: {h.get('status','?')}", GREEN))
        except Exception as e:
            print(c(f"  [ERR] Cannot reach server: {e}", RED))
            print(c("  Tip: Run  python main.py  in another terminal", YELLOW))
            sys.exit(1)

        # ---------- Tools ----------
        tools = env.list_tools()
        print(c(f"\n  MCP Tools ({len(tools)}):", MAGENTA))
        for t in tools:
            print(c(f"     [{t['name']}] {t['description'][:65]}...", MAGENTA))

        # ---------- Options ----------
        opts_resp = env.call_tool("get_available_options")
        bonuses = opts_resp.get("difficulty_bonus", {})
        print(c("\n  Difficulty Bonuses:", YELLOW))
        for d, b in bonuses.items():
            print(c(f"     {d:8s} : +{b} per correct email", YELLOW))

        print(c(f"\n  Dashboard: {base_url}/dashboard", CYAN))
        print(c(f"  API Docs : {base_url}/docs\n", CYAN))

        # ---------- Run episodes ----------
        results = []
        ep_num = 1

        if mode == "all":
            combos = [
                ("easy",   False),
                ("medium", False),
                ("hard",   False),
                ("hard",   True),   # hard + partial info
            ]
        else:
            combos = [(mode, use_partial)]

        for difficulty, partial_info in combos:
            ep_reward, ep_avg = run_episode(env, difficulty, partial_info, seed + ep_num, ep_num)
            results.append((difficulty, partial_info, ep_reward, ep_avg))
            ep_num += 1

        # ---------- Leaderboard ----------
        lb_resp = env.call_tool("get_leaderboard")
        lb = lb_resp.get("leaderboard", [])
        if lb:
            subheader("Session Leaderboard")
            medals = ["[1st]", "[2nd]", "[3rd]"]
            for i, entry in enumerate(lb):
                medal = medals[i] if i < 3 else f"[{i+1}th]"
                diff_str = entry['difficulty'].upper()
                partial_str = " [PARTIAL]" if entry.get("partial_info") else ""
                avg = entry["average_reward"]
                col = GREEN if avg >= 0.8 else (YELLOW if avg >= 0.6 else RED)
                print(c(f"  {medal} {avg:.4f} avg | {diff_str}{partial_str} | {entry['episode_length']} emails", col))

        # ---------- Overall summary ----------
        header("Overall Summary")
        total_avg = sum(r[3] for r in results) / len(results)
        for diff, partial, total, avg in results:
            p = "[PARTIAL]" if partial else ""
            col = GREEN if avg >= 0.8 else (YELLOW if avg >= 0.6 else RED)
            print(c(f"  {diff:8s} {p:9s}  total={total:.4f}  avg={avg:.4f}", col))

        overall_grade = "A" if total_avg >= 0.8 else ("B" if total_avg >= 0.6 else ("C" if total_avg >= 0.4 else "D"))
        grade_col = GREEN if overall_grade in ("A", "B") else RED
        print(c(f"\n  Overall avg  : {total_avg:.4f}", BOLD))
        print(c(f"  Overall grade: {overall_grade}", BOLD + grade_col))
        print()


# ---- Extended client method for difficulty --------------------------------

def _patch_client():
    """Add difficulty param to reset method if not already present."""
    from email_triage_env.client import EmailTriageEnv
    original_reset = EmailTriageEnv.reset

    def reset_v2(self, episode_length=5, seed=None, difficulty="easy", partial_info=False):
        payload = {"episode_length": episode_length, "difficulty": difficulty, "partial_info": partial_info}
        if seed is not None:
            payload["seed"] = seed
        return self._post("/reset", payload)

    EmailTriageEnv.reset = reset_v2


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Email Triage Demo v2")
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--mode", default="all", choices=["all", "easy", "medium", "hard", "mixed"])
    parser.add_argument("--partial", action="store_true", help="Enable partial info mode")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    _patch_client()
    run_demo(base_url=args.url, mode=args.mode, use_partial=args.partial, seed=args.seed)
