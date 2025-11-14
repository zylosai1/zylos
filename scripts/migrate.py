# scripts/migrate.py
"""
Lightweight migration helper.
For production use Alembic. This script will:
- create missing tables (non-destructive)
- print a short summary
"""
from app.database.base import init_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migrate")

def main():
    logger.info("Running lightweight migration (create missing tables)...")
    init_db()
    logger.info("Migration complete. (Use Alembic for structured migrations.)")

if __name__ == "__main__":
    main()