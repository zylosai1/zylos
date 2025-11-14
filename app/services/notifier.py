# app/services/notifier.py
"""
Notifier service:
- in-app push via WebSocket (preferred)
- FCM push for Android (requires server key)
- Email (optional)
This module provides safe wrappers; actual provider keys must be configured via .env.
"""

import logging
from typing import Dict, Any, Optional

from app.services.device_manager import ws_manager
from app.core.config import settings

logger = logging.getLogger("notifier")
logger.setLevel(logging.INFO)

# Optional placeholders for FCM — install pyfcm if you want
try:
    from pyfcm import FCMNotification
except Exception:
    FCMNotification = None

_fcm_client = None
if getattr(settings, "SUPABASE_KEY", None) and FCMNotification is None:
    logger.info("pyfcm not installed; FCM disabled.")

def init_fcm(server_key: str):
    global _fcm_client
    if FCMNotification is None:
        raise RuntimeError("pyfcm not installed")
    _fcm_client = FCMNotification(api_key=server_key)

async def notify_in_app(user_id: str, payload: Dict[str, Any]):
    """
    Preferred: deliver via websocket(s). If user not connected, store or fallback.
    """
    try:
        await ws_manager.send_personal(user_id, payload)
    except Exception:
        logger.exception("In-app notify failed for user %s", user_id)
        # TODO: enqueue to DB for later delivery

def send_fcm(token: str, title: str, body: str, data: Optional[Dict[str, Any]] = None):
    """
    Send FCM push to single device token. Blocks (sync) intentionally simple wrapper.
    """
    if not _fcm_client:
        logger.warning("FCM client not configured")
        return {"error": "fcm-not-configured"}
    try:
        res = _fcm_client.notify_single_device(registration_id=token, message_title=title, message_body=body, data_message=data or {})
        return res
    except Exception as e:
        logger.exception("FCM send failed: %s", e)
        return {"error": str(e)}