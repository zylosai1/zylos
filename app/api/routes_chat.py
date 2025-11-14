# app/api/routes_chat.py

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.security import get_current_user
from app.database.base import get_session
from app.database.schemas import ChatIn
from app.database import crud
from app.ai.brain import process_user_message
from app.services.sync_manager import sync_manager

router = APIRouter(tags=["Chat"], prefix="/chat")


@router.post("/send")
async def send_chat(
    data: ChatIn,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """
    Main chat endpoint → calls Zylos brain → returns the AI reply.
    """

    # Get or create conversation
    conv = crud.get_or_create_conv(session, current_user.id)

    # Store user message
    crud.add_message(session, conv.id, "user", data.text, current_user.id)

    # Run AI brain
    reply = process_user_message(
        user=current_user,
        conversation=conv,
        text=data.text
    )

    # Store AI reply
    msg = crud.add_message(session, conv.id, "zylos", reply)

    # Multi-device sync: push same reply to all connected devices
    await sync_manager.push_reply_to_user(
        current_user.id,
        {"type": "reply", "conversation_id": conv.id, "reply": reply}
    )

    return {
        "reply": reply,
        "message_id": msg.id,
        "conversation_id": conv.id
    }