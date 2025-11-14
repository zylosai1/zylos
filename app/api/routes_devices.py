# app/api/routes_devices.py

from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.core.security import get_current_user
from app.core.utils import uid
from app.database.base import get_session
from app.database.schemas import DeviceRegisterIn, DeviceOut
from app.database import crud

router = APIRouter(tags=["Devices"], prefix="/devices")


# ---------------------------------------------------------
# REGISTER DEVICE
# ---------------------------------------------------------
@router.post("/register", response_model=DeviceOut)
def register_device(
    payload: DeviceRegisterIn,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):

    device_token = uid()

    device = crud.register_device(
        session,
        user_id=current_user.id,
        name=payload.name,
        device_type=payload.device_type,
        token=device_token
    )

    return DeviceOut(device_id=device.id, token=device_token)


# ---------------------------------------------------------
# LIST ALL DEVICES
# ---------------------------------------------------------
@router.get("/list")
def list_devices(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    devices = crud.get_devices_for_user(session, current_user.id)
    return {
        "devices": [
            {
                "id": d.id,
                "name": d.name,
                "type": d.type,
                "last_seen": d.last_seen.isoformat()
            }
            for d in devices
        ]
    }