# app/core/security.py

from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from .config import settings
from typing import Optional
from sqlmodel import Session
from app.database.base import get_session
from app.database.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/token"
)

# ------------------------------------------------------------
# PASSWORD HASHING
# ------------------------------------------------------------
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except:
        return False

# ------------------------------------------------------------
# JWT TOKEN CREATION
# ------------------------------------------------------------
def create_access_token(subject: str, expires_delta: int | None = None):
    expire = datetime.utcnow() + timedelta(
        minutes=(expires_delta or settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {"exp": expire, "sub": str(subject)}

    encoded = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm="HS256"
    )
    return encoded

# ------------------------------------------------------------
# JWT DECODING
# ------------------------------------------------------------
def decode_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload.get("sub")
    except:
        return None

# ------------------------------------------------------------
# CURRENT USER RETRIEVER
# ------------------------------------------------------------
def get_current_user(token: str = Depends(oauth2_scheme)):

    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    with next(get_session()) as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user