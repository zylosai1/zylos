# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.core.config import settings
from app.database.base import init_db
from app.api import (
    routes_auth,
    routes_chat,
    routes_devices,
    routes_memory,
    websocket as ws_router
)

import uvicorn

# ------------------------------------------------------------
# FASTAPI APP INITIALIZATION
# ------------------------------------------------------------
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Zylos AI Backend — Multi-Device, Multi-Agent Intelligent Assistant",
    version="1.0.0"
)

app.mount("/portal", StaticFiles(directory="public"), name="portal")

# ------------------------------------------------------------
# CORS (Frontend Access Control)
# ------------------------------------------------------------
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ------------------------------------------------------------
# INCLUDE API ROUTERS
# ------------------------------------------------------------
app.include_router(routes_auth.router, prefix=f"{settings.API_V1_STR}/auth")
app.include_router(routes_chat.router, prefix=f"{settings.API_V1_STR}/chat")
app.include_router(routes_devices.router, prefix=f"{settings.API_V1_STR}/devices")
app.include_router(routes_memory.router, prefix=f"{settings.API_V1_STR}/memory")

# WebSocket router (NO prefix)
app.include_router(ws_router.router)

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/portal/index.html")

# ------------------------------------------------------------
# INITIALIZE DATABASE
# ------------------------------------------------------------
init_db()

# ------------------------------------------------------------
# MAIN -----------------------------------------------
# ------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
