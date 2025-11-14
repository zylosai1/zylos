# app/database/models.py
from sqlmodel import SQLModel, Field, Column, String
from datetime import datetime
from typing import Optional
import uuid

def uid() -> str:
    return str(uuid.uuid4())

# ---------------------------------------------------------------------
# NOTE:
# - Keep models small and stable; add indices in migrations if needed.
# ---------------------------------------------------------------------

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: str = Field(default_factory=uid, primary_key=True)
    email: str = Field(index=True, nullable=False, unique=True)
    password_hash: str
    name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"
    id: str = Field(default_factory=uid, primary_key=True)
    user_id: str = Field(index=True, nullable=False)
    title: Optional[str] = "Chat"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Message(SQLModel, table=True):
    __tablename__ = "messages"
    id: str = Field(default_factory=uid, primary_key=True)
    conversation_id: str = Field(index=True, nullable=False)
    user_id: Optional[str] = Field(default=None, index=True)
    role: str  # "user" | "zylos" | "system"
    text: str
    metadata: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Device(SQLModel, table=True):
    __tablename__ = "devices"
    id: str = Field(default_factory=uid, primary_key=True)
    user_id: Optional[str] = Field(default=None, index=True)
    name: Optional[str] = None
    type: Optional[str] = None  # "android" / "windows" / "web"
    token: Optional[str] = None
    capabilities: Optional[str] = None  # JSON string describing capabilities
    last_seen: datetime = Field(default_factory=datetime.utcnow)


class TrainingItem(SQLModel, table=True):
    __tablename__ = "training_items"
    id: str = Field(default_factory=uid, primary_key=True)
    user_id: Optional[str] = None
    prompt: str
    response: str
    approved: bool = False
    source: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)