
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import db

async def wipe_scholarships():
    print("=== WIPING SCHOLARSHIPS COLLECTION ===")
    try:
        # Get all docs
        docs = await db.get_all_scholarships()
        print(f"Found {len(docs)} documents to delete.")
        
        count = 0
        batch = db.db.batch()
        
        for s in docs:
            ref = db.db.collection('scholarships').document(s.id)
            batch.delete(ref)
            count += 1
            
            if count >= 400:
                batch.commit()
                print(f"Deleted batch of {count}...")
                batch = db.db.batch()
                count = 0
                
        if count > 0:
            batch.commit()
            print(f"Deleted final batch of {count}.")
            
        print("Wipe complete.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Auto-wiping database...")
    asyncio.run(wipe_scholarships())
