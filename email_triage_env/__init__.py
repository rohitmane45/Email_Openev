# Copyright (c) 2026. All rights reserved.
# Email Triage Environment for OpenEnv Framework
# Built for Meta PyTorch OpenEnv Hackathon x Scaler School of Technology

"""
Email Triage Environment — An OpenEnv RL environment for intelligent email management.

This environment simulates a realistic corporate email inbox where an AI agent must:
- Detect spam vs. legitimate emails
- Classify emails by category (billing, support, sales, hr, general)
- Assign priority levels (urgent, normal, low)
- Route emails to the correct department
- Select appropriate response templates

MCP Tools:
    - ``get_current_email()``: Retrieve the current email requiring triage
    - ``classify_email(...)``: Submit a triage decision for the current email
    - ``get_available_options()``: List all valid classification options
    - ``get_episode_statistics()``: View current episode performance metrics

Example::

    from email_triage_env import EmailTriageEnv

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

from .client import EmailTriageEnv

__all__ = ["EmailTriageEnv"]
__version__ = "1.0.0"
