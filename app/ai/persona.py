
"""
Persona management for Zylos.
- persona_store: per-user persona id or JSON config
- get_persona_for_user: returns persona key (string) or "default"
You can extend to full persona profiles (tone_strength, sarcasm_level, formality).
"""

from typing import Dict

# Simple in-memory store; persist by moving to DB later.
persona_store: Dict[str, str] = {}

# Default persona spec (string key)
DEFAULT_PERSONA = "friendly_hinglish"

def set_persona_for_user(user_id: str, persona_key: str):
    persona_store[user_id] = persona_key

def get_persona_for_user(user_id: str):
    return persona_store.get(user_id, DEFAULT_PERSONA)