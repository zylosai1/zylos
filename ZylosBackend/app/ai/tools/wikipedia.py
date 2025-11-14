"""
Get a concise Wikipedia summary (English).
"""
import requests

WIKI_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/{}"
REQUEST_TIMEOUT = 6.0

def get_summary(title: str) -> str:
    if not title:
        return "No title provided."
    try:
        # sanitize title for URL
        safe = title.strip().replace(" ", "_")
        resp = requests.get(WIKI_SUMMARY.format(safe), timeout=REQUEST_TIMEOUT)
        if resp.status_code == 404:
            return f"No Wikipedia page found for '{title}'."
        resp.raise_for_status()
        j = resp.json()
        extract = j.get("extract")
        if extract:
            # briefify to first 3 sentences (simple)
            sentences = extract.split(". ")
            excerpt = ". ".join(sentences[:3]).strip()
            if not excerpt.endswith("."):
                excerpt += "."
            return excerpt
        return "No summary available."
    except Exception as e:
        return f"Wikipedia fetch failed: {e}"