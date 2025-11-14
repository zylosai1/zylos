# app/api/routes_persona.py

from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.ai.persona import persona_store

router = APIRouter(tags=["Persona"], prefix="/persona")

@router.post("/set")
def set_persona(name: str, current_user=Depends(get_current_user)):
    """
    Set Zylos personality style for specific user.
    """
    persona_store[current_user.id] = name
    return {"status": "ok", "persona": name}

@router.get("/get")
def get_persona(current_user=Depends(get_current_user)):
    return {"persona": persona_store.get(current_user.id, "default")}