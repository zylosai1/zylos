# app/ai/tools/location.py
"""
Detect user's city using IP (ipinfo.io).
Not 100% accurate when used on server; suitable as a best-effort default.
"""
import requests
from typing import Optional

IPINFO = "https://ipinfo.io/json"
REQUEST_TIMEOUT = 4.0

def get_current_city() -> Optional[str]:
    try:
        resp = requests.get(IPINFO, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        j = resp.json()
        city = j.get("city")
        return city
    except Exception:
        return None