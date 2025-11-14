# app/ai/reflection.py
"""
Reflection module: post-check assistant output and decide if improvement needed.
Currently offers a simple semantic check:
- If LLM output contains 'I don't know' or 'No information' or is too short, trigger a retry.
This can be expanded to BLEU/ROUGE checks or tool-based verification.
"""

from typing import Tuple
import re
from .llm_local import call_local_llm
from .prompt_engine import build_system_prompt

NEGATIVE_PATTERNS = [
    r"\bi don'?t know\b",
    r"\bno information\b",
    r"\bnot available\b",
    r"\bcan't find\b",
    r"\bunable to\b"
]

def needs_reflection(answer: str) -> bool:
    if not answer or len(answer.strip()) < 10:
        return True
    low = answer.lower()
    for p in NEGATIVE_PATTERNS:
        if re.search(p, low):
            return True
    return False

def reflect_and_retry(question: str, last_answer: str, user=None) -> Tuple[bool, str]:
    """
    If reflection decides improvement needed, ask LLM to retry with a focused instruction.
    Returns: (improved_flag, new_answer)
    """
    if not needs_reflection(last_answer):
        return False, last_answer

    system = build_system_prompt(user)
    prompt = (
        f"{system}\nThe previous assistant answer was:\n{last_answer}\n\n"
        f"The user question was:\n{question}\n\n"
        "Please produce a clearer, more helpful answer. If uncertain, propose a next action (e.g., call a tool or ask clarifying question)."
    )
    new = call_local_llm(prompt, max_tokens=400)
    return True, new