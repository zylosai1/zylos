# app/ai/tools/time_date.py
from datetime import datetime
import pytz

def get_current_datetime(tz_name: str | None = None) -> str:
    """
    Returns string representation of current datetime.
    If tz_name is provided (eg 'Asia/Kolkata'), returns localized time.
    """
    try:
        if tz_name:
            tz = pytz.timezone(tz_name)
            return datetime.now(tz).strftime("%d %b %Y, %I:%M %p %Z")
    except Exception:
        pass
    return datetime.utcnow().strftime("%d %b %Y, %I:%M %p UTC")
