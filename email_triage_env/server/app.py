"""
Email Triage Environment -- FastAPI Server (v2)
================================================
New in v2:
  - Difficulty levels  : easy / medium / hard / mixed
  - Partial info mode  : agent sees only subject+sender first;
                         must call reveal_body tool to see full body
                         (costs a -0.05 reward penalty per reveal)
  - Live dashboard     : GET /dashboard  -> beautiful HTML UI
  - More MCP tools     : reveal_body, get_leaderboard
  - Leaderboard        : tracks top scores across episodes
"""

import random
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from ..emails import DIFFICULTY_POOLS

# ─────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────

VALID_OPTIONS: Dict[str, List[str]] = {
    "categories":         ["billing", "support", "sales", "hr", "general"],
    "priorities":         ["urgent", "normal", "low"],
    "departments":        ["finance", "customer_support", "sales", "human_resources", "legal", "none"],
    "response_templates": [
        "billing_info", "billing_escalation", "contract_escalation",
        "password_reset_guide", "hr_policy_info", "interview_scheduling",
        "enterprise_demo_request", "spam_discard", "no_reply_needed", "automated_no_action",
    ],
    "difficulties": ["easy", "medium", "hard", "mixed"],
}

FIELD_WEIGHTS: Dict[str, float] = {
    "is_spam":           0.30,
    "category":          0.20,
    "priority":          0.20,
    "department":        0.15,
    "response_template": 0.15,
}

REVEAL_BODY_PENALTY: float = 0.05   # reward deducted each time body is revealed
DIFFICULTY_BONUS: Dict[str, float] = {
    "easy":   0.0,
    "medium": 0.1,   # bonus per correct email on medium
    "hard":   0.2,   # bonus per correct email on hard
    "mixed":  0.05,
}

# Global leaderboard (in-memory; persists for the server session)
_leaderboard: List[Dict[str, Any]] = []
MAX_LEADERBOARD: int = 10


# ─────────────────────────────────────────────────────────────────
# Reward
# ─────────────────────────────────────────────────────────────────

def compute_reward(
    prediction: Dict[str, Any],
    ground_truth: Dict[str, Any],
    reveal_count: int = 0,
    difficulty: str = "easy",
) -> float:
    base = 0.0
    for field, weight in FIELD_WEIGHTS.items():
        if str(prediction.get(field)).lower() == str(ground_truth.get(field)).lower():
            base += weight
    # Apply reveal penalty
    base = max(0.0, base - reveal_count * REVEAL_BODY_PENALTY)
    # Apply difficulty bonus
    if base >= 0.7:
        base = min(1.0, base + DIFFICULTY_BONUS.get(difficulty, 0.0))
    return round(base, 4)


# ─────────────────────────────────────────────────────────────────
# Episode State
# ─────────────────────────────────────────────────────────────────

class EpisodeState:
    def __init__(
        self,
        episode_length: int = 5,
        difficulty: str = "easy",
        partial_info: bool = False,
    ):
        self.episode_id: str = str(uuid.uuid4())
        self.step: int = 0
        self.episode_length: int = episode_length
        self.difficulty: str = difficulty
        self.partial_info: bool = partial_info
        self.total_reward: float = 0.0
        self.current_reveal_count: int = 0   # reveals for current email
        self.body_revealed: bool = False      # has body been revealed this step?

        pool = DIFFICULTY_POOLS.get(difficulty, DIFFICULTY_POOLS["easy"])
        if len(pool) < episode_length:
            # Allow repeats if pool is smaller than requested length
            self.email_queue: List[Dict[str, Any]] = random.choices(pool, k=episode_length)
        else:
            self.email_queue = random.sample(pool, episode_length)

        self.history: List[Dict[str, Any]] = []
        self.done: bool = False
        self.started_at: str = datetime.utcnow().isoformat()

    @property
    def current_email(self) -> Optional[Dict[str, Any]]:
        if self.step < len(self.email_queue):
            return self.email_queue[self.step]
        return None

    def to_dict(self) -> Dict[str, Any]:
        steps_done = max(self.step, 1)
        return {
            "episode_id":     self.episode_id,
            "step":           self.step,
            "episode_length": self.episode_length,
            "difficulty":     self.difficulty,
            "partial_info":   self.partial_info,
            "total_reward":   round(self.total_reward, 4),
            "average_reward": round(self.total_reward / steps_done, 4),
            "done":           self.done,
            "started_at":     self.started_at,
        }


# Global session store
_episode: Optional[EpisodeState] = None


# ─────────────────────────────────────────────────────────────────
# Pydantic Schemas
# ─────────────────────────────────────────────────────────────────

class ResetRequest(BaseModel):
    episode_length: int   = Field(default=5, ge=1, le=10)
    difficulty: str       = Field(default="easy")
    partial_info: bool    = Field(default=False)
    seed: Optional[int]   = None


class ClassifyEmailRequest(BaseModel):
    is_spam: bool
    category: str
    priority: str
    department: str
    response_template: str


# ─────────────────────────────────────────────────────────────────
# FastAPI App
# ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Email Triage Environment",
    description=(
        "MCP-compatible RL environment for intelligent email triage. "
        "Supports difficulty levels (easy/medium/hard/mixed) and partial-info mode. "
        "Built for the Meta PyTorch OpenEnv Hackathon x Scaler School of Technology."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────

def _field_accuracy(history: List[Dict]) -> Dict[str, float]:
    if not history:
        return {f: 0.0 for f in FIELD_WEIGHTS}
    acc: Dict[str, float] = {}
    for field in FIELD_WEIGHTS:
        correct = sum(
            1 for h in history
            if str(h["prediction"].get(field)).lower() == str(h["ground_truth"].get(field)).lower()
        )
        acc[field] = round(correct / len(history), 4)
    return acc


def _safe_email(email: Dict, hide_body: bool) -> Dict:
    """Return email dict, optionally hiding the body."""
    out = {k: v for k, v in email.items() if k != "ground_truth"}
    if hide_body:
        out["body"] = "[HIDDEN] Call reveal_body tool to read the email body."
        out["body_hidden"] = True
    else:
        out["body_hidden"] = False
    return out


# ─────────────────────────────────────────────────────────────────
# Routes — Core
# ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "email_triage_env", "version": "2.0.0"}


@app.post("/reset")
def reset_episode(req: ResetRequest):
    global _episode
    if req.difficulty not in VALID_OPTIONS["difficulties"]:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid difficulty '{req.difficulty}'. Choose from {VALID_OPTIONS['difficulties']}",
        )
    if req.seed is not None:
        random.seed(req.seed)
    _episode = EpisodeState(
        episode_length=req.episode_length,
        difficulty=req.difficulty,
        partial_info=req.partial_info,
    )
    obs = _safe_email(
        _episode.current_email,
        hide_body=_episode.partial_info,
    ) if _episode.current_email else {}
    return {
        "observation": obs,
        "state": _episode.to_dict(),
        "message": (
            f"Episode started. Difficulty: {req.difficulty}. "
            f"Partial info: {req.partial_info}. "
            "Use /tools/get_current_email to retrieve the first email."
        ),
    }


@app.get("/state")
def get_state():
    if _episode is None:
        raise HTTPException(status_code=400, detail="No active episode. Call /reset first.")
    return _episode.to_dict()


# ─────────────────────────────────────────────────────────────────
# Routes — MCP Tools
# ─────────────────────────────────────────────────────────────────

@app.get("/tools")
def list_tools():
    return {
        "tools": [
            {
                "name": "get_current_email",
                "description": (
                    "Retrieve the current email. In partial_info mode, body is hidden. "
                    "Returns id, subject, sender, and body (or placeholder)."
                ),
                "inputSchema": {"type": "object", "properties": {}, "required": []},
            },
            {
                "name": "reveal_body",
                "description": (
                    "Reveal the full body of the current email (partial_info mode only). "
                    "Costs a -0.05 reward penalty. Each call to this tool once per email."
                ),
                "inputSchema": {"type": "object", "properties": {}, "required": []},
            },
            {
                "name": "classify_email",
                "description": "Submit triage decision for current email. Returns reward and next state.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "is_spam":           {"type": "boolean"},
                        "category":          {"type": "string", "enum": VALID_OPTIONS["categories"]},
                        "priority":          {"type": "string", "enum": VALID_OPTIONS["priorities"]},
                        "department":        {"type": "string", "enum": VALID_OPTIONS["departments"]},
                        "response_template": {"type": "string", "enum": VALID_OPTIONS["response_templates"]},
                    },
                    "required": ["is_spam", "category", "priority", "department", "response_template"],
                },
            },
            {
                "name": "get_available_options",
                "description": "List all valid values for each classification field.",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
            },
            {
                "name": "get_episode_statistics",
                "description": "Get performance metrics and history for the current episode.",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
            },
            {
                "name": "get_leaderboard",
                "description": "Get the top scores across all episodes in this session.",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
            },
        ]
    }


@app.post("/tools/get_current_email")
def tool_get_current_email():
    if _episode is None:
        raise HTTPException(status_code=400, detail="No active episode. Call /reset first.")
    if _episode.done:
        raise HTTPException(status_code=400, detail="Episode finished. Call /reset.")
    email = _episode.current_email
    if email is None:
        raise HTTPException(status_code=400, detail="No more emails in queue.")

    hide = _episode.partial_info and not _episode.body_revealed
    return {
        "email":             _safe_email(email, hide_body=hide),
        "emails_remaining":  _episode.episode_length - _episode.step,
        "difficulty":        _episode.difficulty,
        "partial_info_mode": _episode.partial_info,
        "body_revealed":     _episode.body_revealed if _episode.partial_info else None,
    }


@app.post("/tools/reveal_body")
def tool_reveal_body():
    if _episode is None:
        raise HTTPException(status_code=400, detail="No active episode. Call /reset first.")
    if _episode.done:
        raise HTTPException(status_code=400, detail="Episode finished. Call /reset.")
    if not _episode.partial_info:
        raise HTTPException(
            status_code=400,
            detail="reveal_body is only available in partial_info mode. "
                   "Reset with partial_info=true to enable this mode.",
        )
    if _episode.body_revealed:
        return {
            "body":    _episode.current_email["body"],
            "penalty": 0.0,
            "note":    "Body was already revealed for this email. No additional penalty.",
        }
    _episode.body_revealed = True
    _episode.current_reveal_count += 1
    return {
        "body":    _episode.current_email["body"],
        "penalty": REVEAL_BODY_PENALTY,
        "note":    f"Body revealed. A penalty of {REVEAL_BODY_PENALTY} will be applied to this step's reward.",
    }


@app.post("/tools/classify_email")
def tool_classify_email(req: ClassifyEmailRequest):
    if _episode is None:
        raise HTTPException(status_code=400, detail="No active episode. Call /reset first.")
    if _episode.done:
        raise HTTPException(status_code=400, detail="Episode finished. Call /reset.")

    errors = []
    if req.category not in VALID_OPTIONS["categories"]:
        errors.append(f"Invalid category '{req.category}'. Valid: {VALID_OPTIONS['categories']}")
    if req.priority not in VALID_OPTIONS["priorities"]:
        errors.append(f"Invalid priority '{req.priority}'. Valid: {VALID_OPTIONS['priorities']}")
    if req.department not in VALID_OPTIONS["departments"]:
        errors.append(f"Invalid department '{req.department}'. Valid: {VALID_OPTIONS['departments']}")
    if req.response_template not in VALID_OPTIONS["response_templates"]:
        errors.append(f"Invalid response_template. Valid: {VALID_OPTIONS['response_templates']}")
    if errors:
        raise HTTPException(status_code=422, detail=errors)

    current      = _episode.current_email
    ground_truth = current["ground_truth"]
    prediction   = {
        "is_spam": req.is_spam, "category": req.category,
        "priority": req.priority, "department": req.department,
        "response_template": req.response_template,
    }

    reward = compute_reward(
        prediction, ground_truth,
        reveal_count=_episode.current_reveal_count,
        difficulty=_episode.difficulty,
    )
    _episode.total_reward += reward
    _episode.history.append({
        "step":         _episode.step,
        "email_id":     current["id"],
        "difficulty":   current.get("difficulty", _episode.difficulty),
        "prediction":   prediction,
        "ground_truth": ground_truth,
        "reward":       reward,
        "reveals_used": _episode.current_reveal_count,
    })

    _episode.step += 1
    _episode.current_reveal_count = 0
    _episode.body_revealed = False

    if _episode.step >= _episode.episode_length:
        _episode.done = True
        _update_leaderboard(_episode)

    next_email = None
    if not _episode.done and _episode.current_email:
        next_email = _safe_email(_episode.current_email, hide_body=_episode.partial_info)

    return {
        "reward":          reward,
        "done":            _episode.done,
        "step":            _episode.step,
        "total_reward":    round(_episode.total_reward, 4),
        "next_email":      next_email,
        "field_breakdown": {
            field: str(prediction.get(field)).lower() == str(ground_truth.get(field)).lower()
            for field in FIELD_WEIGHTS
        },
    }


@app.post("/tools/get_available_options")
def tool_get_available_options():
    return {
        "options":          VALID_OPTIONS,
        "field_weights":    FIELD_WEIGHTS,
        "reveal_penalty":   REVEAL_BODY_PENALTY,
        "difficulty_bonus": DIFFICULTY_BONUS,
    }


@app.post("/tools/get_episode_statistics")
def tool_get_episode_statistics():
    if _episode is None:
        raise HTTPException(status_code=400, detail="No active episode. Call /reset first.")
    return {
        "state":          _episode.to_dict(),
        "history":        _episode.history,
        "field_accuracy": _field_accuracy(_episode.history),
    }


@app.post("/tools/get_leaderboard")
def tool_get_leaderboard():
    return {"leaderboard": _leaderboard, "total_episodes": len(_leaderboard)}


@app.get("/leaderboard")
def get_leaderboard():
    return {"leaderboard": _leaderboard, "total_episodes": len(_leaderboard)}


def _update_leaderboard(ep: EpisodeState):
    global _leaderboard
    entry = {
        "episode_id":     ep.episode_id,
        "difficulty":     ep.difficulty,
        "partial_info":   ep.partial_info,
        "total_reward":   round(ep.total_reward, 4),
        "average_reward": round(ep.total_reward / max(ep.step, 1), 4),
        "episode_length": ep.episode_length,
        "field_accuracy": _field_accuracy(ep.history),
        "completed_at":   datetime.utcnow().isoformat(),
    }
    _leaderboard.append(entry)
    _leaderboard.sort(key=lambda x: x["average_reward"], reverse=True)
    _leaderboard = _leaderboard[:MAX_LEADERBOARD]


# ─────────────────────────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────────────────────────

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return HTMLResponse(content=_DASHBOARD_HTML)


_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Email Triage Environment - Live Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet"/>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg: #0a0e1a;
      --surface: #111827;
      --surface2: #1a2235;
      --border: #1e2d45;
      --cyan: #00d4ff;
      --purple: #7c3aed;
      --green: #10b981;
      --yellow: #f59e0b;
      --red: #ef4444;
      --text: #e2e8f0;
      --muted: #64748b;
    }
    body {
      font-family: 'Inter', sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
    }
    header {
      background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
      border-bottom: 1px solid var(--border);
      padding: 18px 32px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    header h1 {
      font-size: 1.4rem;
      font-weight: 700;
      background: linear-gradient(90deg, var(--cyan), var(--purple));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .badge {
      font-size: 0.7rem;
      font-weight: 600;
      padding: 3px 10px;
      border-radius: 20px;
      border: 1px solid;
    }
    .badge-live { color: var(--green); border-color: var(--green); animation: pulse 2s infinite; }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.5} }
    .container { max-width: 1400px; margin: 0 auto; padding: 24px 32px; }
    .grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
    .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }
    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
    }
    .card-title {
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: .08em;
      color: var(--muted);
      margin-bottom: 10px;
    }
    .stat {
      font-size: 2rem;
      font-weight: 700;
      line-height: 1;
    }
    .stat-sub { font-size: 0.8rem; color: var(--muted); margin-top: 6px; }
    .cyan   { color: var(--cyan); }
    .purple { color: var(--purple); }
    .green  { color: var(--green); }
    .yellow { color: var(--yellow); }
    .red    { color: var(--red); }

    /* Difficulty badge */
    .diff-badge {
      display: inline-block;
      font-size: 0.72rem;
      font-weight: 700;
      padding: 2px 10px;
      border-radius: 12px;
      text-transform: uppercase;
      letter-spacing: .06em;
    }
    .diff-easy   { background: #052e16; color: var(--green); }
    .diff-medium { background: #451a03; color: var(--yellow); }
    .diff-hard   { background: #450a0a; color: var(--red); }
    .diff-mixed  { background: #1e1b4b; color: var(--purple); }

    /* Field accuracy bars */
    .field-row { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
    .field-label { width: 140px; font-size: 0.8rem; flex-shrink: 0; color: var(--muted); }
    .bar-bg { flex: 1; height: 8px; background: var(--surface2); border-radius: 4px; overflow: hidden; }
    .bar-fill { height: 100%; border-radius: 4px; transition: width .5s ease; }
    .field-pct { width: 40px; text-align: right; font-size: 0.8rem; font-weight: 600; }

    /* History table */
    table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
    th { text-align: left; padding: 8px 12px; border-bottom: 1px solid var(--border); color: var(--muted); font-weight: 600; font-size: 0.72rem; text-transform: uppercase; letter-spacing: .06em; }
    td { padding: 10px 12px; border-bottom: 1px solid var(--border); vertical-align: top; }
    tr:hover td { background: var(--surface2); }
    .correct { color: var(--green); font-weight: 600; }
    .wrong   { color: var(--red); }

    /* Leaderboard */
    .lb-row { display: flex; align-items: center; gap: 12px; padding: 10px 0; border-bottom: 1px solid var(--border); }
    .lb-rank { width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: 700; flex-shrink: 0; }
    .rank-1 { background: linear-gradient(135deg, #f59e0b, #d97706); color: #000; }
    .rank-2 { background: linear-gradient(135deg, #94a3b8, #64748b); color: #000; }
    .rank-3 { background: linear-gradient(135deg, #a16207, #854d0e); color: #fff; }
    .rank-n { background: var(--surface2); color: var(--muted); }
    .lb-info { flex: 1; }
    .lb-score { font-size: 1.1rem; font-weight: 700; }

    /* No data state */
    .no-data { text-align: center; padding: 40px; color: var(--muted); font-size: 0.9rem; }

    /* Status dot */
    .status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 6px; }
    .dot-green { background: var(--green); }
    .dot-yellow { background: var(--yellow); }

    .chart-wrap { position: relative; height: 200px; }
  </style>
</head>
<body>
<header>
  <h1>Email Triage Environment</h1>
  <div style="display:flex;align-items:center;gap:16px;">
    <span class="badge badge-live">LIVE</span>
    <span style="font-size:0.8rem;color:var(--muted);">Auto-refresh: 2s</span>
  </div>
</header>

<div class="container">

  <!-- KPI Cards -->
  <div class="grid-4" id="kpi-grid">
    <div class="card">
      <div class="card-title">Current Episode Step</div>
      <div class="stat cyan" id="kpi-step">--</div>
      <div class="stat-sub" id="kpi-length">of -- emails</div>
    </div>
    <div class="card">
      <div class="card-title">Total Reward</div>
      <div class="stat green" id="kpi-reward">--</div>
      <div class="stat-sub" id="kpi-avg">avg per email: --</div>
    </div>
    <div class="card">
      <div class="card-title">Difficulty</div>
      <div class="stat" id="kpi-diff">--</div>
      <div class="stat-sub" id="kpi-partial">--</div>
    </div>
    <div class="card">
      <div class="card-title">Episode Status</div>
      <div class="stat" id="kpi-status">--</div>
      <div class="stat-sub" id="kpi-episode-id" style="font-size:0.65rem;word-break:break-all;"></div>
    </div>
  </div>

  <!-- Reward Chart + Field Accuracy -->
  <div class="grid-2">
    <div class="card">
      <div class="card-title">Cumulative Reward per Step</div>
      <div class="chart-wrap">
        <canvas id="rewardChart"></canvas>
      </div>
    </div>
    <div class="card">
      <div class="card-title">Field Accuracy</div>
      <div id="field-bars" style="margin-top:12px;">
        <div class="no-data" id="field-nodata">No data yet. Start an episode.</div>
      </div>
    </div>
  </div>

  <!-- History Table + Leaderboard -->
  <div class="grid-2">
    <div class="card">
      <div class="card-title">Episode History</div>
      <div style="overflow-x:auto;max-height:320px;overflow-y:auto;">
        <table id="history-table">
          <thead>
            <tr>
              <th>#</th><th>Email</th><th>Reward</th><th>Spam</th><th>Category</th><th>Priority</th>
            </tr>
          </thead>
          <tbody id="history-body">
            <tr><td colspan="6" class="no-data">No history yet.</td></tr>
          </tbody>
        </table>
      </div>
    </div>
    <div class="card">
      <div class="card-title">Session Leaderboard (Top 10)</div>
      <div id="leaderboard-list">
        <div class="no-data">No completed episodes yet.</div>
      </div>
    </div>
  </div>

</div>

<script>
const BASE = window.location.origin;

// Chart setup
const ctx = document.getElementById('rewardChart').getContext('2d');
const rewardChart = new Chart(ctx, {
  type: 'line',
  data: {
    labels: [],
    datasets: [{
      label: 'Cumulative Reward',
      data: [],
      borderColor: '#00d4ff',
      backgroundColor: 'rgba(0,212,255,0.08)',
      borderWidth: 2,
      pointRadius: 4,
      pointBackgroundColor: '#00d4ff',
      tension: 0.3,
      fill: true,
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 300 },
    scales: {
      x: { grid: { color: '#1e2d45' }, ticks: { color: '#64748b' } },
      y: { grid: { color: '#1e2d45' }, ticks: { color: '#64748b' }, beginAtZero: true }
    },
    plugins: {
      legend: { display: false },
      tooltip: { backgroundColor: '#1a2235', titleColor: '#e2e8f0', bodyColor: '#94a3b8' }
    }
  }
});

function diffBadge(d) {
  const cls = 'diff-' + d;
  return `<span class="diff-badge ${cls}">${d}</span>`;
}

function barColor(pct) {
  if (pct >= 0.8) return '#10b981';
  if (pct >= 0.5) return '#f59e0b';
  return '#ef4444';
}

function rankClass(i) {
  if (i === 0) return 'rank-1';
  if (i === 1) return 'rank-2';
  if (i === 2) return 'rank-3';
  return 'rank-n';
}

async function refresh() {
  // State
  try {
    const state = await fetch(BASE + '/state').then(r => r.ok ? r.json() : null);
    if (state) {
      document.getElementById('kpi-step').textContent = state.step;
      document.getElementById('kpi-length').textContent = `of ${state.episode_length} emails`;
      document.getElementById('kpi-reward').textContent = state.total_reward.toFixed(4);
      document.getElementById('kpi-avg').textContent = `avg per email: ${state.average_reward.toFixed(4)}`;

      const diffEl = document.getElementById('kpi-diff');
      diffEl.innerHTML = diffBadge(state.difficulty);

      document.getElementById('kpi-partial').textContent =
        state.partial_info ? 'Partial Info Mode ON' : 'Full Info Mode';

      const statusEl = document.getElementById('kpi-status');
      if (state.done) {
        statusEl.innerHTML = '<span class="status-dot dot-yellow"></span>Done';
        statusEl.className = 'stat yellow';
      } else {
        statusEl.innerHTML = '<span class="status-dot dot-green"></span>Running';
        statusEl.className = 'stat green';
      }
      document.getElementById('kpi-episode-id').textContent = state.episode_id;
    }
  } catch(_) {}

  // Stats + history + chart
  try {
    const resp = await fetch(BASE + '/tools/get_episode_statistics', { method: 'POST', headers: {'Content-Type':'application/json'}, body: '{}' });
    if (resp.ok) {
      const data = await resp.json();
      const history = data.history || [];
      const acc = data.field_accuracy || {};

      // Field accuracy bars
      const container = document.getElementById('field-bars');
      const nodata = document.getElementById('field-nodata');
      if (history.length > 0) {
        nodata && (nodata.style.display = 'none');
        const fields = Object.entries(acc);
        container.innerHTML = fields.map(([field, pct]) => `
          <div class="field-row">
            <span class="field-label">${field}</span>
            <div class="bar-bg"><div class="bar-fill" style="width:${(pct*100).toFixed(0)}%;background:${barColor(pct)};"></div></div>
            <span class="field-pct" style="color:${barColor(pct)}">${(pct*100).toFixed(0)}%</span>
          </div>`).join('');
      }

      // Chart
      const labels = history.map(h => `Step ${h.step + 1}`);
      let cumulative = 0;
      const cumData = history.map(h => { cumulative += h.reward; return +cumulative.toFixed(4); });
      rewardChart.data.labels = labels;
      rewardChart.data.datasets[0].data = cumData;
      rewardChart.update('none');

      // History table
      const tbody = document.getElementById('history-body');
      if (history.length > 0) {
        tbody.innerHTML = history.map(h => {
          const bd = h.field_breakdown || {};
          const correct = h.reward >= 0.95;
          const gt = h.ground_truth || {};
          return `<tr>
            <td>${h.step + 1}</td>
            <td style="color:var(--cyan);font-size:0.75rem">${h.email_id}</td>
            <td class="${h.reward >= 0.7 ? 'correct' : 'wrong'}">${h.reward.toFixed(4)}</td>
            <td class="${h.prediction.is_spam === gt.is_spam ? 'correct' : 'wrong'}">${h.prediction.is_spam ? 'Spam' : 'Legit'}</td>
            <td class="${h.prediction.category === gt.category ? 'correct' : 'wrong'}">${h.prediction.category}</td>
            <td class="${h.prediction.priority === gt.priority ? 'correct' : 'wrong'}">${h.prediction.priority}</td>
          </tr>`;
        }).join('');
      }
    }
  } catch(_) {}

  // Leaderboard
  try {
    const lb = await fetch(BASE + '/leaderboard').then(r => r.json());
    const list = lb.leaderboard || [];
    const el = document.getElementById('leaderboard-list');
    if (list.length === 0) {
      el.innerHTML = '<div class="no-data">No completed episodes yet.</div>';
    } else {
      el.innerHTML = list.map((entry, i) => `
        <div class="lb-row">
          <div class="lb-rank ${rankClass(i)}">${i+1}</div>
          <div class="lb-info">
            <div style="font-size:0.75rem;color:var(--muted);margin-bottom:2px;">
              ${diffBadge(entry.difficulty)} ${entry.partial_info ? '<span style="color:var(--purple);font-size:0.7rem;margin-left:4px;">Partial</span>' : ''}
            </div>
            <div style="font-size:0.7rem;color:var(--muted);">${entry.episode_length} emails</div>
          </div>
          <div>
            <div class="lb-score" style="color:${entry.average_reward>=0.8?'var(--green)':entry.average_reward>=0.5?'var(--yellow)':'var(--red)'}">
              ${entry.average_reward.toFixed(4)}
            </div>
            <div style="font-size:0.7rem;color:var(--muted);">avg reward</div>
          </div>
        </div>`).join('');
    }
  } catch(_) {}
}

refresh();
setInterval(refresh, 2000);
</script>
</body>
</html>"""
