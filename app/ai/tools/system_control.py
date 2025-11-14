# app/ai/tools/system_control.py
"""
System control tool (safe stub).

WARNING:
This module is a controlled interface. Do NOT execute arbitrary shell commands
provided by users. Real device control should be implemented inside device agents
(Windows/Android) that authenticate and accept signed commands from the backend.

Here we provide:
- run_command(action, params) -> simulated result or a safe queuing for agent
"""

import json
from typing import Dict, Any

# In-memory queue (simple). For production use Redis / persistent queue.
COMMAND_QUEUE = []

ALLOWED_ACTIONS = {
    "open_app": ["app_name"],
    "screenshot": [],
    "click": ["x", "y"],
    "type": ["text"],
    "shutdown": [],
    "restart": []
}

def run_command(action: str, params: Dict[str, Any] = None) -> str:
    params = params or {}
    if action not in ALLOWED_ACTIONS:
        return f"Action '{action}' is not permitted."
    # Validate params keys
    required = ALLOWED_ACTIONS[action]
    for r in required:
        if r not in params:
            return f"Missing param '{r}' for action '{action}'."

    # Enqueue command for devices to pick up (device agent will poll or get via WS)
    cmd = {"action": action, "params": params}
    COMMAND_QUEUE.append(cmd)
    # For now return a safe acknowledgement
    return f"Enqueued action '{action}'. Device will execute if authorized."