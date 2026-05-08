import asyncio
import sys
import os

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import db
from app.models import Scholarship
import structlog

logger = structlog.get_logger()

async def diagnose_system():
    """
    Diagnose the state of the system:
    1. Count Scholarships in Firestore
    2. Check a sample scholarship for data integrity (name, amount, tags)
    3. Verify User Profile existence (for matching)
    """
    print("🩺 STARTING SYSTEM DIAGNOSIS...")
    
    # 1. Firestore Check
    print("\n[1] Checking Firestore Data...")
    try:
        docs = db.db.collection('scholarships').stream()
        scholarships = [d.to_dict() for d in docs]
        count = len(scholarships)
        print(f"   ✅ Firestore contains {count} scholarships.")
        
        if count > 0:
            sample = scholarships[0]
            print(f"   🔎 Sample: {sample.get('name', 'NO NAME')} | ID: {sample.get('id')} | Amount: {sample.get('amount')}")
            
            # Check for critical fields
            missing = []
            for field in ['name', 'url', 'deadline', 'id']:
                if not sample.get(field) and not sample.get('source_url'): # url fallback
                    missing.append(field)
            
            if missing:
                print(f"   ⚠️ WARNING: Sample is missing fields: {missing}")
            else:
                print("   ✅ Sample data structure looks valid.")
        else:
            print("   ❌ CRITICAL: Database is empty! Scrape failed to persist or Purge wiped everything.")

    except Exception as e:
        print(f"   ❌ Firestore Connection Failed: {e}")

    # 2. User Profile Check
    print("\n[2] Checking User Profiles...")
    try:
        users = db.db.collection('users').stream()
        user_count = sum(1 for _ in users)
        print(f"   ℹ️ Found {user_count} user profiles.")
    except Exception as e:
        print(f"   ❌ User DB Check Failed: {e}")

    print("\n✨ DIAGNOSIS COMPLETE.")

if __name__ == "__main__":
    asyncio.run(diagnose_system())
