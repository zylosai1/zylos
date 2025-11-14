# scripts/init_db.py
"""
Initialize DB and required folders.
Run once after clone / on deploy.
"""
import os
from pathlib import Path
import logging

from app.database.base import init_db, DB_MODE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("init_db")

def main():
    logger.info("Creating folders...")
    Path("app/data").mkdir(parents=True, exist_ok=True)
    Path("app/logs").mkdir(parents=True, exist_ok=True)
    logger.info("Initializing database (mode=%s)...", DB_MODE)
    init_db()
    logger.info("Done.")

if __name__ == "__main__":
    main()