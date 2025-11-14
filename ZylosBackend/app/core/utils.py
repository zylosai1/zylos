# app/core/utils.py

import uuid
from datetime import datetime

# ------------------------------------------------------------
# UNIVERSAL ID GENERATOR
# ------------------------------------------------------------
def uid() -> str:
    return str(uuid.uuid4())

# ------------------------------------------------------------
# UTC TIMESTAMP
# ------------------------------------------------------------
def now_iso():
    return datetime.utcnow().isoformat() + "Z"

# ------------------------------------------------------------
# TIMESTAMP (human readable)
# ------------------------------------------------------------
def hr_time():
    return datetime.utcnow().strftime("%d %b %Y, %I:%M %p UTC")