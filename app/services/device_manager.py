# app/services/device_manager.py
"""
WebSocket manager that tracks multiple device sockets per user.
Provides:
- connect(user_id, websocket)
- disconnect(user_id, websocket)
- send_personal(user_id, payload)  # send to all devices of a user
- send_to_device(user_id, device_id, payload)
Optional: Redis pub/sub integration for multi-instance broadcasting.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional

try:
    import aioredis
except Exception:
    aioredis = None

from fastapi import WebSocket

from app.core.config import settings

logger = logging.getLogger("device_manager")
logger.setLevel(logging.INFO)


class InMemoryWSManager:
    def __init__(self):
        # user_id -> list of websockets
        self.active: Dict[str, List[WebSocket]] = {}
        # user_id -> dict device_id -> websocket (if devices supply id)
        self.device_map: Dict[str, Dict[str, WebSocket]] = {}
        self.lock = asyncio.Lock()

    async def connect(self, user_id: str, websocket: WebSocket, device_id: Optional[str] = None):
        """
        Register websocket under user_id. Optionally associate a device_id.
        """
        await websocket.accept()
        async with self.lock:
            self.active.setdefault(user_id, []).append(websocket)
            if device_id:
                self.device_map.setdefault(user_id, {})[device_id] = websocket
        logger.info("WS connect user=%s device=%s sockets=%d", user_id, device_id, len(self.active.get(user_id, [])))

    async def disconnect(self, user_id: str, websocket: WebSocket):
        async with self.lock:
            conns = self.active.get(user_id, [])
            if websocket in conns:
                conns.remove(websocket)
            # remove from device_map if present
            for devmap in (self.device_map.get(user_id, {}),):
                for did, ws in list(devmap.items()):
                    if ws == websocket:
                        devmap.pop(did, None)
            if not conns:
                self.active.pop(user_id, None)
                self.device_map.pop(user_id, None)
        logger.info("WS disconnect user=%s remaining=%d", user_id, len(self.active.get(user_id, [])) if user_id in self.active else 0)

    async def send_personal(self, user_id: str, payload: dict):
        """
        Send payload to all active websockets for user_id.
        """
        conns = list(self.active.get(user_id, []))
        if not conns:
            logger.debug("No active sockets for user %s", user_id)
            return
        msg = json.dumps(payload)
        for ws in list(conns):
            try:
                await ws.send_text(msg)
            except Exception as e:
                logger.exception("Failed sending to websocket for user %s: %s", user_id, e)
                # best-effort cleanup
                await self.disconnect(user_id, ws)

    async def send_to_device(self, user_id: str, device_id: str, payload: dict):
        devmap = self.device_map.get(user_id, {})
        ws = devmap.get(device_id)
        if not ws:
            logger.debug("Device %s for user %s not connected", device_id, user_id)
            return
        try:
            await ws.send_json(payload)
        except Exception:
            await self.disconnect(user_id, ws)

# Instantiate in-memory manager
ws_manager = InMemoryWSManager()


# Optional Redis-backed pubsub for multi-instance scaling
class RedisPubSubBridge:
    def __init__(self, redis_url: Optional[str]):
        self.redis_url = redis_url
        self._pub = None
        self._sub = None
        self._task = None

    async def start(self):
        if not aioredis or not self.redis_url:
            logger.info("Redis pubsub not available or not configured.")
            return
        try:
            self._pub = await aioredis.from_url(self.redis_url, encoding="utf-8", decode_responses=True)
            self._sub = self._pub  # using same client for convenience
            self._task = asyncio.create_task(self._listen())
            logger.info("RedisPubSubBridge started.")
        except Exception as e:
            logger.exception("RedisPubSubBridge init failed: %s", e)

    async def publish_user(self, user_id: str, payload: dict):
        if not self._pub:
            return
        channel = f"zylos:user:{user_id}"
        await self._pub.publish(channel, json.dumps(payload))

    async def _listen(self):
        # subscribe to pattern "zylos:user:*"
        try:
            pubsub = self._pub.pubsub()
            await pubsub.psubscribe("zylos:user:*")
            async for message in pubsub.listen():
                if message is None:
                    continue
                typ = message.get("type")
                if typ not in ("message", "pmessage"):
                    continue
                data = message.get("data")
                if not data:
                    continue
                try:
                    payload = json.loads(data)
                    channel = message.get("channel") or message.get("pattern")
                    # extract user id from channel name
                    # channel like "zylos:user:{user_id}"
                    parts = channel.split(":")
                    user_id = parts[-1]
                    # forward to local ws_manager
                    await ws_manager.send_personal(user_id, payload)
                except Exception:
                    logger.exception("RedisPubSubBridge failed process msg")
        except Exception:
            logger.exception("RedisPubSubBridge listener crashed")


redis_bridge = RedisPubSubBridge(settings.REDIS_URL if getattr(settings, "REDIS_URL", None) else None)