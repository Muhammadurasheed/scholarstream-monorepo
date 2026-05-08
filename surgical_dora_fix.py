import asyncio
from app.database import db
import logging

logging.basicConfig(level=logging.INFO)

async def migrate_broken_dora_urls():
    """
    Surgically correct ALL broken DoraHacks URLs across 2000+ documents.
    """
    print("Starting Surgical DoraHacks URL Migration...")
    
    # Scan ALL scholarships (since organization names vary)
    docs = db.db.collection('scholarships').get()
    print(f"Analyzing {len(docs)} documents...")
    
    updated_count = 0
    batch = db.db.batch()
    batch_size = 0
    
    for doc in docs:
        data = doc.to_dict()
        url = str(data.get('source_url', ''))
        original_url = url
        
        # Logic: If it contains /bounty but NOT /bugbounty, it's likely a DoraHacks 404
        # We only apply this to dorahacks.io domains to be safe
        if 'dorahacks.io' in url:
            if '/bounty' in url and '/bugbounty' not in url:
                url = url.replace('/bounty', '/bugbounty')
            
        if url != original_url:
            title = str(data.get('title', 'Unknown')).encode('ascii', 'ignore').decode('ascii')
            print(f"  [FIX] {title[:40]:<40} | From: {original_url} -> {url}")
            
            doc_ref = db.db.collection('scholarships').document(doc.id)
            batch.update(doc_ref, {'source_url': url})
            updated_count += 1
            batch_size += 1
            
            # Commit in chunks of 400 (Firestore limit is 500)
            if batch_size >= 400:
                batch.commit()
                batch = db.db.batch()
                batch_size = 0

    if batch_size > 0:
        batch.commit()

    print(f"\nMigration Complete! Updated {updated_count} documents.")

if __name__ == "__main__":
    asyncio.run(migrate_broken_dora_urls())
