"""
ScholarStream Firestore Cleanup Script
=====================================
One-time script to clear corrupted/duplicate data from Firestore.

Run via: python -m backend.cleanup_script
"""
import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import firebase_admin
from firebase_admin import credentials, firestore
import structlog

logger = structlog.get_logger()


def init_firebase():
    """Initialize Firebase Admin SDK using app config"""
    try:
        firebase_admin.get_app()
        logger.info("Firebase already initialized")
    except ValueError:
        # Use same config as main app
        from app.config import settings
        cred = credentials.Certificate(settings.firebase_credentials)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase initialized from app config")
    
    return firestore.client()


def delete_collection(db, collection_name: str, batch_size: int = 500) -> int:
    """Delete all documents in a collection"""
    collection_ref = db.collection(collection_name)
    docs = collection_ref.limit(batch_size).stream()
    deleted = 0
    
    batch = db.batch()
    batch_count = 0
    
    for doc in docs:
        batch.delete(doc.reference)
        batch_count += 1
        deleted += 1
        
        if batch_count >= batch_size:
            batch.commit()
            batch = db.batch()
            batch_count = 0
            logger.info(f"Deleted {deleted} docs from {collection_name}...")
            # Recursively delete more
            deleted += delete_collection(db, collection_name, batch_size)
            return deleted
    
    if batch_count > 0:
        batch.commit()
    
    return deleted


def main():
    print("=" * 60)
    print("[CLEANUP] ScholarStream Firestore Cleanup Script")
    print("=" * 60)
    print()
    print("This script will DELETE all data from:")
    print("  - scholarships collection")
    print("  - user_matches collection")
    print()
    
    confirm = input("Are you sure you want to proceed? (type 'YES' to confirm): ")
    
    if confirm != 'YES':
        print("Aborted.")
        return
    
    print()
    print("Initializing Firebase...")
    db = init_firebase()
    
    print()
    print("[DELETE] Deleting scholarships collection...")
    scholarships_deleted = delete_collection(db, 'scholarships')
    print(f"   [OK] Deleted {scholarships_deleted} scholarship documents")
    
    print()
    print("[DELETE] Deleting user_matches collection...")
    matches_deleted = delete_collection(db, 'user_matches')
    print(f"   [OK] Deleted {matches_deleted} user_matches documents")
    
    print()
    print("=" * 60)
    print("[DONE] Cleanup Complete!")
    print(f"   Total documents deleted: {scholarships_deleted + matches_deleted}")
    print()
    print("Next steps:")
    print("  1. Restart the backend server")
    print("  2. The scraper will automatically repopulate with clean data")
    print("=" * 60)


if __name__ == "__main__":
    main()
