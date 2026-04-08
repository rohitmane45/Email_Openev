---
title: Email Triage OpenEnv
emoji: 📧
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Email Triage OpenEnv Environment

OpenEnv-compatible environment for training and evaluating agents on enterprise inbox triage.

Agents must classify each email over five dimensions:

- spam or not spam
- intent category
- priority level
- routing department
- response template

## Environment Description

This environment follows a deterministic RL-style loop:

1. `POST /reset` with episode settings.
2. Read the current observation (email).
3. Send an action with 5-field classification.
4. Receive reward and transition until episode completion.

Difficulty modes:

- easy
- medium
- hard
- mixed

Partial information mode can hide the email body (`body_hidden=true`) until the agent calls `POST /tools/reveal_body`. Each reveal applies a reward penalty.

## Observation Space

Each step observation is one email object:

```json
{
  "id": "string",
  "subject": "string",
  "sender": "string",
  "body": "string",
  "body_hidden": false,
  "difficulty": "easy|medium|hard|mixed"
}
```

Notes:

- `body_hidden=true` means body text is masked in the current step.
- Use `POST /tools/reveal_body` to reveal the body (with penalty).

## Action Space

Action payload for each step:

```json
{
  "is_spam": true,
  "category": "billing|support|sales|hr|general",
  "priority": "urgent|normal|low",
  "department": "finance|customer_support|sales|human_resources|legal|none",
  "response_template": "billing_info|billing_escalation|contract_escalation|password_reset_guide|hr_policy_info|interview_scheduling|enterprise_demo_request|spam_discard|no_reply_needed|automated_no_action"
}
```

## Reward Model

Step reward is bounded in `[0.0, 1.0]`.

Weighted base score:

- `is_spam`: `0.30`
- `category`: `0.20`
- `priority`: `0.20`
- `department`: `0.15`
- `response_template`: `0.15`

Adjustments:

- reveal penalty: `-0.05` per reveal on current email
- difficulty bonus (if base score is at least `0.7`):
- easy: `+0.00`
- medium: `+0.10`
- hard: `+0.20`
- mixed: `+0.05`

## API Endpoints

Core:

- `POST /reset`
- `POST /step`
- `GET /state`
- `GET /tasks`
- `GET /health`

Tools:

- `POST /tools/get_current_email`
- `POST /tools/reveal_body`
- `POST /tools/classify_email`
- `POST /tools/get_available_options`
- `POST /tools/get_episode_statistics`
- `POST /tools/get_leaderboard`

UI:

- `GET /dashboard`
- `GET /docs`

## Local Setup

### 1) Install dependencies

```bash
pip install -r requirements.txt
```

### 2) Run server

```bash
python main.py --host 0.0.0.0 --port 8000
```

### 3) Verify

- Dashboard: `http://localhost:8000/dashboard`
- OpenAPI docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

## Docker (Local)

Build image:

```bash
docker build -t email-triage-openenv .
```

Run container:

```bash
docker run --rm -e PORT=8000 -p 8000:8000 email-triage-openenv
```

Check health:

```bash
curl http://localhost:8000/health
```

## Deploy to Hugging Face Spaces (Docker)

### 1) Create Space

- Create a new Hugging Face Space.
- Select `Docker` as SDK.

### 2) Push repository

Include at minimum:

- `Dockerfile`
- `README.md`
- `requirements.txt`
- environment source code

The README frontmatter is configured for Spaces:

- `sdk: docker`
- `app_port: 7860`

### 3) Runtime behavior

Container command:

```bash
uvicorn email_triage_env.server.app:app --host ${HOST} --port ${PORT}
```

Defaults in Dockerfile:

- `HOST=0.0.0.0`
- `PORT=7860`

Spaces can inject its own `PORT`; the container respects it.

### 4) Post-deploy checks

- `/health` returns `{"status":"ok"}`.
- `/docs` is reachable.
- `/` redirects to `/dashboard`.

## Baseline Inference

Run after server startup:

```bash
python inference.py
```

Required environment variables:

- `API_BASE_URL`
- `MODEL_NAME`
- `HF_TOKEN`
- `OPENAI_API_KEY`

Optional:

- `ENV_BASE_URL` (default `http://localhost:8000`)

## Project Artifacts

- `openenv.yaml`: environment metadata and API schemas
- `inference.py`: baseline evaluator
- `email_triage_env/server/app.py`: FastAPI server
- `email_triage_env/openenv_env.py`: environment implementation
