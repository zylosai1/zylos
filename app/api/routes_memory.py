# app/api/routes_memory.py

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.security import get_current_user
from app.database.base import get_session
from app.database import crud
from app.database.models import Message
from sqlmodel import select

router = APIRouter(tags=["Memory"], prefix="/memory")


@router.get("/recent")
def get_recent_memory(
    limit: int = 30,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """
    Returns user's recent messages.
    """

    query = select(Message).where(
        Message.user_id == current_user.id
    ).order_by(Message.timestamp.desc()).limit(limit)

    rows = session.exec(query).all()

    return {
        "history": [
            {
                "id": m.id,
                "role": m.role,
                "text": m.text,
                "timestamp": m.timestamp.isoformat()
            }
            for m in rows
        ]
    }