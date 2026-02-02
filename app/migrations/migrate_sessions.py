"""
Database Migration: Add Sessions Support
Run this script once to prepare the database for session management
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.mongodb_service import get_db
from app.core.logging import logger


def migrate_sessions():
    """Create sessions collection and indexes"""
    db = get_db()
    if db is None:
        logger.error("[Migration] Database unavailable")
        return False
    
    try:
        # Create sessions collection if it doesn't exist
        if "sessions" not in db.list_collection_names():
            db.create_collection("sessions")
            logger.info("[Migration] Created sessions collection")
        
        # Create indexes
        db.sessions.create_index("session_id", unique=True)
        db.sessions.create_index([("user_id", 1), ("active", 1)])
        db.sessions.create_index("last_active")
        
        logger.info("[Migration] Created sessions indexes")
        
        # Create TTL index to auto-delete old sessions after 30 days
        db.sessions.create_index("last_active", expireAfterSeconds=2592000)  # 30 days
        logger.info("[Migration] Created TTL index for session cleanup")
        
        return True
    
    except Exception as e:
        logger.error(f"[Migration] Error: {e}", exc_info=True)
        return False


def main():
    logger.info("[Migration] Starting session management migration...")
    
    if migrate_sessions():
        logger.info("[Migration] ✅ Migration completed successfully")
    else:
        logger.error("[Migration] ❌ Migration failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
