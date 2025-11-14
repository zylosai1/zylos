# app/services/sync_manager.py
"""
SyncManager: ensures the SAME reply is delivered to all devices of a user.
If Redis is configured, publishes to Redis channel for multi-host delivery.
"""

import asyncio
import logging
from typing import Dict

from app.services import device_manager
from app.core.config import settings

logger = logging.getLogger("sync_manager")
logger.setLevel(logging.INFO)

# simple in-memory queue per user to serialize messages
_user_locks: Dict[str, asyncio.Lock] = {}

class SyncManager:
    def __init__(self):
        self.ws_manager = device_manager.ws_manager
        self.redis_bridge = device_manager.redis_bridge

    async def push_reply_to_user(self, user_id: str, payload: dict):
        """
        Push the same payload to all devices for user_id.
        Uses local WS manager and optionally publishes to Redis for other instances.
        """
        lock = _user_locks.setdefault(user_id, asyncio.Lock())
        async with lock:
            # First try local websocket delivery
            try:
                await self.ws_manager.send_personal(user_id, payload)
            except Exception:
                logger.exception("Local push failed for user %s", user_id)
            # Then publish to Redis channel so other instances get it too
            try:
                if self.redis_bridge and self.redis_bridge.redis_url:
                    await self.redis_bridge.publish_user(user_id, payload)
            except Exception:
                logger.exception("Redis publish failed for user %s", user_id)

sync_manager = SyncManager()