# app/services/scheduler.py
"""
Background scheduler for Zylos tasks.
- cleanup memory daily
- rebuild index periodically (if requested)
- trigger training jobs (when enough training items approved)
This file is intended to be run as a background process (see run.sh)
"""

import time
import logging
from datetime import datetime, timedelta

from app.ai.memory_engine import cleanup_memory, summarize_user_memory
from app.ai.trainer import schedule_training
from app.database.vector_store import vector_store

logger = logging.getLogger("zylos.scheduler")
logger.setLevel(logging.INFO)

DEFAULT_POLL_SECONDS = 60 * 60  # run hourly by default

def run_scheduler(poll_seconds: int = DEFAULT_POLL_SECONDS):
    logger.info("Scheduler started, poll_seconds=%s", poll_seconds)
    last_cleanup = datetime.utcnow() - timedelta(days=1)
    last_index = datetime.utcnow() - timedelta(days=1)
    while True:
        try:
            now = datetime.utcnow()
            # DAILY CLEANUP
            if (now - last_cleanup) > timedelta(days=1):
                logger.info("Running daily memory cleanup...")
                removed = cleanup_memory(max_age_days=365, keep_recent_per_user=200)
                logger.info("Memory cleanup removed=%s users", removed)
                last_cleanup = now

            # PERIODIC INDEX SAVE (if vector store exists)
            if vector_store and hasattr(vector_store, "save") and (now - last_index) > timedelta(hours=6):
                try:
                    logger.info("Saving vector store index...")
                    vector_store.save()
                    last_index = now
                except Exception:
                    logger.exception("Failed to save vector store")

            # TRAINING SCHEDULER (run short check hourly)
            # You may change conditions to trigger training.
            try:
                schedule_training()
            except Exception:
                logger.exception("Training scheduler failed (nonfatal)")

        except Exception:
            logger.exception("Scheduler main loop exception")
        # sleep until next iteration
        time.sleep(poll_seconds)

if __name__ == "__main__":
    run_scheduler()