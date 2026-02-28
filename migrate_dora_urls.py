import sys
import os
import asyncio

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Force environment variables for Firestore initialization if needed
# (Assuming credentials are already available via settings)
from app.database import db
import structlog

logger = structlog.get_logger()

async def migrate_dorahacks_urls():
    """
    Surgically correct DoraHacks URLs in the database.
    """
    print("Starting DoraHacks URL Migration...")
    
    # Query all DoraHacks entries
    docs = db.db.collection('scholarships').where('organization', '==', 'DoraHacks').get()
    
    if not docs:
        print("No DoraHacks documents found.")
        return

    print(f"Found {len(docs)} DoraHacks documents. Analyzing...")
    
    updated_count = 0
    batch = db.db.batch() # Use firestore batch for efficiency
    batch_size = 0
    
    for doc in docs:
        data = doc.to_dict()
        url = data.get('source_url', '')
        original_url = url
        
        if not url:
            continue
            
        # 1. Correct /bounty to /bugbounty
        # Use replace selectively or regex to avoid double-correcting already correct ones
        if '/bounty' in url and '/bugbounty' not in url:
            url = url.replace('/bounty', '/bugbounty')
            
        # 3. Ensure no trailing slashes if they cause issues
        # (Optional, but good for normalization)
        
            print(f"  [FIX] Correcting: {data.get('title')}")
            print(f"     From: {original_url}")
            print(f"     To:   {url}")
            
            doc_ref = db.db.collection('scholarships').document(doc.id)
            batch.update(doc_ref, {'source_url': url})
            updated_count += 1
            batch_size += 1
            
            # Commit batch every 100 items
            if batch_size >= 100:
                batch.commit()
                batch = db.db.batch()
                batch_size = 0

    if batch_size > 0:
        batch.commit()

    print(f"\nMigration Complete!")
    print(f"Updated {updated_count} documents.")

if __name__ == "__main__":
    asyncio.run(migrate_dorahacks_urls())
