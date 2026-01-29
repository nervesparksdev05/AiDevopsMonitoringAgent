"""
MongoDB Service
Database connection and operations
"""
from __future__ import annotations

from pymongo import MongoClient
from app.core.config import MONGO_URI, DB_NAME, MAX_DOCS
from app.core.logging import logger


_mongo_client = None
_db_connected = False


def get_db():
    """Get MongoDB database connection"""
    global _mongo_client, _db_connected
    try:
        uri = (MONGO_URI or "").strip()
        if not uri:
            logger.error("[MongoDB Error] MONGO_URI not set")
            return None

        if _mongo_client is None:
            logger.info("[MongoDB] Connecting...")
            _mongo_client = MongoClient(
                uri,
                serverSelectionTimeoutMS=2000,
                connectTimeoutMS=2000,
                socketTimeoutMS=2000,
                maxPoolSize=5,
            )
            _db_connected = False

        if not _db_connected:
            _mongo_client[DB_NAME].list_collection_names()
            _db_connected = True
            logger.info("[MongoDB] Connected!")

        return _mongo_client[DB_NAME]
    except Exception as e:
        logger.error(f"[MongoDB Error] {e}")
        _mongo_client = None
        _db_connected = False
        return None


def _pick_sort_field(sample: dict) -> str:
    """Pick a reasonable timestamp field for cleanup ordering."""
    for f in ("timestamp", "created_at", "collected_at", "last_activity", "window_end"):
        if f in sample:
            return f
    return "_id"


def cleanup_collection(db, collection: str, sort_field: str | None = None):
    """Remove old documents from a collection to maintain size limit (MAX_DOCS)."""
    try:
        count = db[collection].count_documents({})
        if count <= MAX_DOCS:
            return

        sample = db[collection].find_one({})
        sf = sort_field or (_pick_sort_field(sample or {}))
        remove_n = max(0, count - MAX_DOCS)
        old = list(db[collection].find().sort(sf, 1).limit(remove_n))
        if old:
            db[collection].delete_many({"_id": {"$in": [d["_id"] for d in old]}})
            logger.info(f"[cleanup] Removed {len(old)} old docs from {collection}")
    except Exception as e:
        logger.error(f"[cleanup] Error cleaning {collection}: {e}")
