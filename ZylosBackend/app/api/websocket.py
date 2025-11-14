# app/api/websocket.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.device_manager import ws_manager

router = APIRouter()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    Multi-device WebSocket → one user_id can have multiple devices.

    All devices under same user_id will receive identical AI replies.
    """
    await ws_manager.connect(user_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()

            # simple ping-pong
            if data.get("type") == "ping":
                await ws_manager.send_personal(user_id, {"type": "pong"})

    except WebSocketDisconnect:
        await ws_manager.disconnect(user_id)