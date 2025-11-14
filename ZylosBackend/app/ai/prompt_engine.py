"""
Prompt builder for Zylos.
Responsible for:
- System prompt (persona + rules)
- Context injection: last N messages, long-term memory snippets
- Tool specification (for function-calling style prompts)
- Final prompt assembly for LLM calls
"""

from datetime import datetime
from ..core.config import settings
from .persona import get_persona_for_user
from ..ai.tools.location import get_current_city
from typing import List, Dict, Any

# Tools metadata (name, description, signature) — used for instructing LLM
TOOLS_METADATA = [
    {
        "name": "weather",
        "description": "Get current weather info for a city. Input: city name string. Returns short text.",
        "parameters": {"city": "string"}
    },
    {
        "name": "search",
        "description": "General-purpose web search (DuckDuckGo instant answers). Input: query string. Returns text summary.",
        "parameters": {"query": "string"}
    },
    {
        "name": "wikipedia",
        "description": "Get a short Wikipedia summary for a topic/title.",
        "parameters": {"title": "string"}
    },
    {
        "name": "youtube",
        "description": "Search YouTube (via Piped). Input: query, optional limit (int). Returns list of results.",
        "parameters": {"query": "string", "limit": "int"}
    },
    {
        "name": "system_control",
        "description": "Request a system/device action (safe stub). Input: action string and params dict.",
        "parameters": {"action": "string", "params": "object"}
    },
    {
        "name": "time_date",
        "description": "Return current datetime string, optionally timezone-aware.",
        "parameters": {"tz_name": "string"}
    }
]

def build_system_prompt(user=None) -> str:
    """
    Returns the system-level prompt that guides LLM persona and behavior.
    Insert persona rules, allowed tools, and general reasoning instructions.
    """
    now = datetime.utcnow().strftime("%d %b %Y, %I:%M %p UTC")
    city = get_current_city() or "Unknown"
    persona_name = get_persona_for_user(user.id) if user else "default"
    persona_text = (
        "You are Zylos — a helpful, witty, polite Indian assistant. "
        "Speak in a natural mix of Hindi (Devanagari) and English (Hinglish). "
        "Be concise, context-aware, and prefer actionable responses."
    )

    tools_list = "\n".join([f"- {t['name']}: {t['description']}" for t in TOOLS_METADATA])

    system = (
        f"{persona_text}\n"
        f"Persona: {persona_name}\n"
        f"Date: {now}\n"
        f"Detected city (server-side best-effort): {city}\n\n"
        f"TOOLS AVAILABLE:\n{tools_list}\n\n"
        "RULES:\n"
        "- If a user question can be answered exactly by calling a tool, CALL THE TOOL and return the tool output in the assistant message.\n"
        "- When calling tools, prefer minimal and precise inputs (no long text dumps).\n"
        "- Prefer friendly, helpful Hinglish; use Devanagari for Hindi words.\n"
        "- If uncertain or the tool fails, be transparent and propose a fallback step.\n"
    )
    return system

def build_prompt_with_context(system_prompt: str, short_history: List[Dict[str, str]], user_input: str, memory_snippets: List[str] = []) -> str:
    """
    Build the final prompt to be sent to the LLM.
    - short_history: list of dicts with keys {role: 'user'|'assistant'|'system', text: ...}
    - memory_snippets: list of strings from long-term memory to include for context.
    """
    parts = [system_prompt]
    if memory_snippets:
        parts.append("RELEVANT MEMORY (short):")
        for s in memory_snippets:
            parts.append(f"- {s}")

    if short_history:
        parts.append("CONVERSATION HISTORY (most recent first):")
        for msg in short_history[-8:]:
            role = msg.get("role", "user")
            text = msg.get("text", "")
            parts.append(f"{role.upper()}: {text}")

    parts.append("USER: " + user_input.strip())
    parts.append("\nASSISTANT:")
    return "\n\n".join(parts)