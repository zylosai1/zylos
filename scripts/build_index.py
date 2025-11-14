# scripts/build_index.py
"""
Rebuild or save vector index. If you want to re-embed long memories,
use the add() API on vector_store. This script uses vector_store.save() to persist.
"""
import logging
from app.database.vector_store import vector_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("build_index")

def main():
    logger.info("Saving vector store index...")
    try:
        vector_store.save()
        logger.info("Index saved.")
    except Exception:
        logger.exception("Failed to save vector store index.")

if __name__ == "__main__":
    main()