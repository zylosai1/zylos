
"""
Planner: Breaks complex user goals into steps, chooses tools, and returns a plan.
Two modes:
- Heuristic quick-check (fast path)
- LLM-assisted plan (when heuristics insufficient)
"""

from typing import Dict, Any, List
from .tools.tool_router import call_tool
from .prompt_engine import build_system_prompt
from .llm_local import call_local_llm

# simple heuristics to detect task types for now
KEYWORD_TOOL_MAP = {
    "weather": "weather",
    "temperature": "weather",
    "rain": "weather",
    "open youtube": "youtube",
    "youtube": "youtube",
    "who is": "wikipedia",
    "define": "wikipedia",
    "search": "search",
    "find": "search",
    "play": "system_control",
    "shutdown": "system_control",
    "screenshot": "system_control"
}

def detect_tool_from_text(text: str) -> str | None:
    t = text.lower()
    for k, v in KEYWORD_TOOL_MAP.items():
        if k in t:
            return v
    return None

def simple_plan(text: str) -> Dict[str, Any]:
    """
    Returns a simple plan dict:
    {
        "plan_type": "tool"|"llm",
        "steps":[ {"action":"call_tool", "tool":"weather", "args":{"city":"Mumbai"}} ... ]
    }
    """
    tool = detect_tool_from_text(text)
    if tool:
        # simple mapping for weather where city may be last token
        if tool == "weather":
            # attempt to extract city (naive)
            parts = text.strip().split()
            city = parts[-1].strip().strip(".?,")
            return {"plan_type": "tool", "steps": [{"action":"call_tool", "tool":"weather", "args":{"city": city}}]}
        elif tool == "youtube":
            query = text
            return {"plan_type":"tool", "steps":[{"action":"call_tool", "tool":"youtube", "args":{"query": query}}]}
        elif tool == "wikipedia":
            # extract probable topic
            topic = text.replace("who is", "").replace("who's", "").strip()
            return {"plan_type":"tool", "steps":[{"action":"call_tool", "tool":"wikipedia", "args":{"title": topic}}]}
        else:
            # generic
            return {"plan_type":"tool", "steps":[{"action":"call_tool", "tool":tool, "args":{"text": text}}]}
    # fallback to LLM plan
    return {"plan_type":"llm", "steps": [{"action":"llm_reason", "args":{"text": text}}]}

def llm_plan(text: str, user=None) -> Dict[str, Any]:
    """
    Ask LLM to propose a step-by-step plan with possible tool calls in JSON-like text.
    Keep prompt minimal and parse naive JSON from model output.
    """
    system = build_system_prompt(user)
    prompt = system + "\n\nTask: Break the following user request into a short plan (3-6 steps). For steps that require calling an available tool, indicate step as: CALL_TOOL(tool_name, json_args). Return plan as bullet points.\n\nUser request:\n" + text + "\n\nPlan:"
    out = call_local_llm(prompt, max_tokens=300)
    # naive parse: we will return text as 'llm_plan_text' and let the caller interpret or call tools manually
    return {"plan_type":"llm", "llm_plan_text": out}