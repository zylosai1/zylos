# app/api/routes_auth.py

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.database.base import get_session
from app.database.schemas import RegisterIn, LoginIn, TokenOut
from app.database import crud
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token
)

router = APIRouter(tags=["Auth"], prefix="/auth")


# ---------------------------------------------------------
# REGISTER USER
# ---------------------------------------------------------
@router.post("/register", response_model=TokenOut)
def register(payload: RegisterIn, session: Session = Depends(get_session)):

    # check existing
    user = crud.get_user_by_email(session, payload.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    hashed = get_password_hash(payload.password)
    user = crud.create_user(
        session,
        email=payload.email,
        password_hash=hashed,
        name=payload.name
    )

    token = create_access_token(user.id)

    return TokenOut(token=token, user_id=user.id)


# ---------------------------------------------------------
# LOGIN USER
# ---------------------------------------------------------
@router.post("/token", response_model=TokenOut)
def login(payload: LoginIn, session: Session = Depends(get_session)):

    user = crud.get_user_by_email(session, payload.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user.id)

    return TokenOut(token=token, user_id=user.id)