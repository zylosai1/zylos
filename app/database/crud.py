# app/database/crud.py
from typing import Optional, List, Dict
from sqlmodel import select, Session
from datetime import datetime
from .models import User, Conversation, Message, Device, TrainingItem
from .base import DB_MODE

# -------------------------
# USER helpers (SQL mode)
# -------------------------
def get_user_by_email_sql(session: Session, email: str) -> Optional[User]:
    return session.exec(select(User).where(User.email == email)).first()

def get_user_by_id_sql(session: Session, user_id: str) -> Optional[User]:
    return session.get(User, user_id)

def create_user_sql(session: Session, email: str, password_hash: str, name: Optional[str] = None) -> User:
    user = User(email=email, password_hash=password_hash, name=name)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

# -------------------------
# CONVERSATION helpers
# -------------------------
def get_or_create_conv_sql(session: Session, user_id: str) -> Conversation:
    conv = session.exec(select(Conversation).where(Conversation.user_id == user_id)).first()
    if conv:
        return conv
    conv = Conversation(user_id=user_id, title="Chat")
    session.add(conv)
    session.commit()
    session.refresh(conv)
    return conv

# -------------------------
# MESSAGE helpers
# -------------------------
def add_message_sql(session: Session, conversation_id: str, role: str, text: str, user_id: Optional[str] = None, meta: Optional[str] = None) -> Message:
    m = Message(conversation_id=conversation_id, user_id=user_id, role=role, text=text, meta=meta)
    session.add(m)
    session.commit()
    session.refresh(m)
    return m

def get_last_messages_sql(session: Session, conversation_id: str, limit: int = 50) -> List[Message]:
    q = session.exec(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.timestamp.desc()).limit(limit)
    ).all()
    return list(reversed(q))  # oldest -> newest

# -------------------------
# DEVICE helpers
# -------------------------
def register_device_sql(session: Session, user_id: str, name: Optional[str], device_type: Optional[str], token: str) -> Device:
    d = Device(user_id=user_id, name=name, type=device_type, token=token)
    session.add(d)
    session.commit()
    session.refresh(d)
    return d

def get_devices_for_user_sql(session: Session, user_id: str) -> List[Device]:
    return session.exec(select(Device).where(Device.user_id == user_id)).all()

def update_device_last_seen_sql(session: Session, device_id: str):
    d = session.get(Device, device_id)
    if d:
        d.last_seen = datetime.utcnow()
        session.add(d)
        session.commit()
        session.refresh(d)
    return d

# -------------------------
# TRAINING ITEMS
# -------------------------
def add_training_item_sql(session: Session, prompt: str, response: str, user_id: Optional[str] = None, source: Optional[str] = None, approved: bool = False) -> TrainingItem:
    t = TrainingItem(user_id=user_id, prompt=prompt, response=response, source=source, approved=approved)
    session..add(t)
    session.commit()
    session.refresh(t)
    return t

def list_approved_training_sql(session: Session) -> List[TrainingItem]:
    return session.exec(select(TrainingItem).where(TrainingItem.approved == True)).all()

# -------------------------
# DISPATCHERS (High-level APIs)
# -------------------------
def get_user_by_email(session_or_db, email: str):
    """
    Dispatcher: in SQL mode session_or_db is Session.
    """
    if DB_MODE in ("sqlite", "supabase"):
        return get_user_by_email_sql(session_or_db, email)
    else:
        raise NotImplementedError("Only SQL DB_MODE supported in this CRUD implementation.")

def create_user(session_or_db, email: str, password_hash: str, name: Optional[str] = None):
    if DB_MODE in ("sqlite", "supabase"):
        return create_user_sql(session_or_db, email, password_hash, name)
    else:
        raise NotImplementedError("Only SQL DB_MODE supported in this CRUD implementation.")

def get_or_create_conv(session_or_db, user_id: str):
    if DB_MODE in ("sqlite", "supabase"):
        return get_or_create_conv_sql(session_or_db, user_id)
    else:
        raise NotImplementedError("Only SQL DB_MODE supported in this CRUD implementation.")

def add_message(session_or_db, conv_id: str, role: str, text: str, user_id: Optional[str] = None, meta: Optional[str] = None):
    if DB_MODE in ("sqlite", "supabase"):
        return add_message_sql(session_or_db, conv_id, role, text, user_id, meta)
    else:
        raise NotImplementedError("Only SQL DB_MODE supported in this CRUD implementation.")

def get_last_messages(session_or_db, conv_id: str, limit: int = 50):
    if DB_MODE in ("sqlite", "supabase"):
        return get_last_messages_sql(session_or_db, conv_id, limit)
    else:
        raise NotImplementedError("Only SQL DB_MODE supported in this CRUD implementation.")

def register_device(session_or_db, user_id: str, name: Optional[str], device_type: Optional[str], token: str):
    if DB_MODE in ("sqlite", "supabase"):
        return register_device_sql(session_or_db, user_id, name, device_type, token)
    else:
        raise NotImplementedError("Only SQL DB_MODE supported in this CRUD implementation.")

def get_devices_for_user(session_or_db, user_id: str):
    if DB_MODE in ("sqlite", "supabase"):
        return get_devices_for_user_sql(session_or_db, user_id)
    else:
        raise NotImplementedError("Only SQL DB_MODE supported in this CRUD implementation.")
