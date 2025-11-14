"""
YouTube search via Piped proxy API (no API key).
Returns list of title — channel.
"""
import requests
from typing import List

PIPED_SEARCH = "https://piped.video/api/v1/search"
REQUEST_TIMEOUT = 6.0

def search_youtube(query: str, limit: int = 5) -> str:
    if not query:
        return "No query provided."
    try:
        resp = requests.get(PIPED_SEARCH, params={"q": query}, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        j = resp.json()
        items = j.get("items") or j.get("videos") or j.get("results") or []
        results: List[str] = []
        for it in items[:limit]:
            title = it.get("title") or it.get("name")
            channel = it.get("author") or it.get("uploader") or it.get("channel")
            if title and channel:
                results.append(f"{title} — {channel}")
            elif title:
                results.append(title)
        if not results:
            return "No YouTube results found."
        return "\n".join(results)
    except Exception as e:
        return f"YouTube search failed: {e}"