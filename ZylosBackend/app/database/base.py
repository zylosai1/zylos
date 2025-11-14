# app/database/base.py
from pathlib import Path
from typing import Generator
import os

from sqlmodel import create_engine, Session
from ..core.config import settings

# Ensure data folder exists
Path("app/data").mkdir(parents=True, exist_ok=True)

DB_MODE = (settings.DATABASE_MODE or "sqlite").lower()

# SQLite (default) uses check_same_thread; Postgres does not.
if DB_MODE in ("sqlite", "supabase"):
    print(f"[db.base] Initializing SQL DB (mode={DB_MODE})")
    database_url = settings.DATABASE_URL

    # For sqlite we pass check_same_thread
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    engine = create_engine(database_url, echo=False, connect_args=connect_args)

    def get_session() -> Generator[Session, None, None]:
        """
        Yield a SQLModel Session. Use as a FastAPI dependency.
        """
        with Session(engine) as session:
            yield session

    def init_db() -> None:
        """
        Create SQL tables (if using SQL). Import models lazily to avoid circular imports.
        """
        from .models import SQLModel  # SQLModel metadata includes all models
        SQLModel.metadata.create_all(engine)
        print("[db.base] SQLModel metadata created (tables initialized)")

else:
    raise ValueError(f"Unsupported DATABASE_MODE: {DB_MODE}")