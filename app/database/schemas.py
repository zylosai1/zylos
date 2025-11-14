# app/database/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class RegisterIn(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None

class TokenOut(BaseModel):
    token: str
    user_id: str

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class ChatIn(BaseModel):
    conversation_id: Optional[str] = None
    text: str

class MessageOut(BaseModel):
    id: str
    conversation_id: str
    user_id: Optional[str]
    role: str
    text: str
    timestamp: str

class DeviceRegisterIn(BaseModel):
    name: Optional[str]
    device_type: Optional[str]

class DeviceOut(BaseModel):
    device_id: str
    token: str