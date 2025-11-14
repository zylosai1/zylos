"""
DuckDuckGo Instant Answer tool (no API key).
If instant answer is missing, it returns short related topics.
"""

import requests
from typing import Optional

DDG_URL = "https://api.duckduckgo.com/"
REQUEST_TIMEOUT = 6.0

def duckduck_search(query: str) -> str:
    if not query:
        return "No query provided."
    try:
        resp = requests.get(DDG_URL, params={"q": query, "format":"json", "no_redirect":"1"}, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        j = resp.json()
        abstract = j.get("AbstractText")
        if abstract:
            return abstract
        # fallback: use RelatedTopics
        related = j.get("RelatedTopics", [])
        texts = []
        for item in related[:4]:
            if isinstance(item, dict):
                t = item.get("Text") or item.get("Result") or ""
                if t:
                    texts.append(t)
            elif isinstance(item, list):
                # nested list case
                for sub in item[:2]:
                    if isinstance(sub, dict) and sub.get("Text"):
                        texts.append(sub.get("Text"))
        if texts:
            return "\n".join(texts)
        return "No short answer found. Try a more specific query."
    except Exception as e:
        return f"Search failed: {e}"