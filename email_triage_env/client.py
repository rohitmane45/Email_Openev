"""
Email Triage Environment Client
================================
Python client for the Email Triage MCP Environment server.
Works with or without the `openenv` package installed.
"""

import json
from typing import Any, Dict, List, Optional

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class EmailTriageEnv:
    """
    Client for the Email Triage FastAPI environment server.

    Usage::

        with EmailTriageEnv(base_url="http://localhost:8000") as env:
            env.reset()
            tools = env.list_tools()
            email = env.call_tool("get_current_email")
            result = env.call_tool(
                "classify_email",
                is_spam=False,
                category="billing",
                priority="urgent",
                department="finance",
                response_template="billing_escalation",
            )
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        if not HAS_REQUESTS:
            raise ImportError(
                "The 'requests' package is required. Install it with: pip install requests"
            )
        self.base_url = base_url.rstrip("/")
        self._session: Optional[requests.Session] = None

    # ── Context manager support ──────────────────────────

    def __enter__(self):
        self._session = requests.Session()
        return self

    def __exit__(self, *args):
        if self._session:
            self._session.close()
            self._session = None

    # ── Internal HTTP helpers ────────────────────────────

    def _get(self, path: str) -> Dict[str, Any]:
        sess = self._session or requests
        resp = sess.get(f"{self.base_url}{path}", timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, payload: Optional[Dict] = None) -> Dict[str, Any]:
        sess = self._session or requests
        resp = sess.post(
            f"{self.base_url}{path}",
            json=payload or {},
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    # ── Public API ───────────────────────────────────────

    def health(self) -> Dict[str, Any]:
        """Check if the server is alive."""
        return self._get("/health")

    def reset(
        self,
        episode_length: int = 5,
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Start a new episode."""
        payload: Dict[str, Any] = {"episode_length": episode_length}
        if seed is not None:
            payload["seed"] = seed
        return self._post("/reset", payload)

    def state(self) -> Dict[str, Any]:
        """Get current episode state."""
        return self._get("/state")

    def list_tools(self) -> List[Dict[str, Any]]:
        """Discover available MCP tools."""
        return self._get("/tools")["tools"]

    def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Call an MCP tool by name.

        Args:
            tool_name: One of 'get_current_email', 'classify_email',
                       'get_available_options', 'get_episode_statistics'
            **kwargs:  Tool-specific arguments (for classify_email).

        Returns:
            Tool response as a dict.
        """
        return self._post(f"/tools/{tool_name}", kwargs if kwargs else {})

    # ── Convenience wrappers ─────────────────────────────

    def get_current_email(self) -> Dict[str, Any]:
        return self.call_tool("get_current_email")

    def classify_email(
        self,
        is_spam: bool,
        category: str,
        priority: str,
        department: str,
        response_template: str,
    ) -> Dict[str, Any]:
        return self.call_tool(
            "classify_email",
            is_spam=is_spam,
            category=category,
            priority=priority,
            department=department,
            response_template=response_template,
        )

    def get_available_options(self) -> Dict[str, Any]:
        return self.call_tool("get_available_options")

    def get_episode_statistics(self) -> Dict[str, Any]:
        return self.call_tool("get_episode_statistics")
