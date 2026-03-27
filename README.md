# 📬 Email Triage Environment v2.0

> **Meta PyTorch OpenEnv Hackathon × Scaler School of Technology**

An MCP-compatible Reinforcement Learning environment that simulates a corporate email inbox. An AI agent must intelligently triage incoming emails — detecting spam, classifying by category, setting priority, routing to the right department, and selecting the response template.

🔥 **New in v2.0:**
- **Difficulty Levels** (Easy, Medium, Hard, Mixed) with adversarial emails.
- **Partial Info Mode** (Agent only sees the subject line initially and must decide whether to take a reward penalty to reveal the body).
- **Live Leaderboard & Dashboard** (`http://localhost:8000/dashboard`).

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the server
```bash
python main.py
```
Server starts at `http://localhost:8000`
- **Live Dashboard**: http://localhost:8000/dashboard
- **API Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

### 3. Run the demo agent
```bash
# (in a second terminal)
python demo.py --mode all
```
*Note: The demo has an intentional 3-second delay per decision so you can watch the Live Dashboard update in real-time!*

---

## 💻 Live Dashboard

The environment includes a built-in real-time monitoring dashboard!
While an agent is running, open `http://localhost:8000/dashboard` in your browser to see:
*   Live step-by-step reward chart
*   Real-time field accuracy bars
*   Episode email history
*   Session-wide top 10 Leaderboard

---

## 🐳 Docker (Hugging Face Spaces Ready)

```bash
# Build
docker build -t email-triage-env .

# Run
docker run -p 8000:8000 email-triage-env
```
*(You can upload this repository directly to a Hugging Face Docker Space for instant cloud deployment).*

---

## 🧠 Environment Design

### Task
Triage emails across 5 dimensions:

| Field | Options | Weight |
|-------|---------|--------|
| `is_spam` | `true / false` | 30% |
| `category` | `billing, support, sales, hr, general` | 20% |
| `priority` | `urgent, normal, low` | 20% |
| `department` | `finance, customer_support, sales, human_resources, legal, none` | 15% |
| `response_template` | 10 templates | 15% |

### Reward & Scoring
*   **Base Reward:** Each step returns a reward in `[0.0, 1.0]` based on weighted accuracy.
*   **Difficulty Bonus:** Correct classifications on Hard (+0.2) or Medium (+0.1) grant bonus points.
*   **Partial Info Penalty:** If `partial_info=True`, calling the `reveal_body` tool costs `-0.05` points. Agents must learn to triage purely from the subject line when possible.

---

## 🔧 MCP Tools

| Tool | Description |
|------|-------------|
| `get_current_email` | Get the email currently in queue (Body hidden if `partial_info` is True). |
| `reveal_body` | Unhides the email body. Costs -0.05 reward. |
| `classify_email` | Submit triage decision, get reward. |
| `get_available_options` | List all valid field values and difficulty bonuses. |
| `get_episode_statistics` | Get full episode stats & step history. |
| `get_leaderboard` | View the top 10 agent scores for the session. |

### Reset episode
```json
POST /reset
{
  "episode_length": 5, 
  "difficulty": "hard",
  "partial_info": true,
  "seed": 42
}
```

---

## 📁 Project Structure

```
email_triage_env/         # Main environment package
├── __init__.py           
├── emails.py             # Dataset categorized by difficulty
├── client.py             # Python HTTP client
└── server/
    ├── app.py            # FastAPI server (Dashboard, MCP tools, Grading)

main.py                   # Server entry point
demo.py                   # Rule-based reference agent (for testing)
requirements.txt          # Python dependencies
Dockerfile                # Container config
README.md                 # This file
```

---

*Built for the Meta PyTorch OpenEnv Hackathon × Scaler School of Technology*
