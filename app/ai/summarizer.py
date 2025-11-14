from typing import List
from .llm_local import call_local_llm

def summarize_text(text: str, max_tokens: int = 200) -> str:
    prompt = (
        "You are a concise summarizer. Summarize the following content in Hinglish (mix of Devanagari Hindi and English), "
        "one paragraph, 2-4 sentences, friendly tone:\n\n"
        f"{text}\n\nSummary:"
    )
    return call_local_llm(prompt, max_tokens=max_tokens)