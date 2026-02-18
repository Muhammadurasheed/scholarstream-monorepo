import asyncio
import sys
import os

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import db
from app.config import settings
import structlog

logger = structlog.get_logger()

async def purge_data():
    """
    Purge all data from:
    1. scholarships collection
    2. user_matches collection
    
    This ensures a clean slate for the new scraper logic to populate.
    """
    print(f"STARTING NUCLEAR PURGE on Project: {settings.firebase_project_id}")
    
    # 1. Purge Scholarships
    print("   -> Deleting all scholarships...")
    docs = db.db.collection('scholarships').stream()
    count = 0
    batch = db.db.batch()
    
    for doc in docs:
        batch.delete(doc.reference)
        count += 1
        if count % 400 == 0:
            batch.commit()
            batch = db.db.batch()
            print(f"      ... deleted {count} docs")
            
    batch.commit()
    print(f"Deleted {count} total scholarships.")
    
    # 2. Purge User Matches
    print("   -> Deleting all user matches...")
    docs = db.db.collection('user_matches').stream()
    count = 0
    batch = db.db.batch()
    
    for doc in docs:
        batch.delete(doc.reference)
        count += 1
        if count % 400 == 0:
            batch.commit()
            batch = db.db.batch()
    
    batch.commit()
    print(f"Deleted {count} user match records.")
    
    print("PURGE COMPLETE. The system is clean.")

if __name__ == "__main__":
    asyncio.run(purge_data())
