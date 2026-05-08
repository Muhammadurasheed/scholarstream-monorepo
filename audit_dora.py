import asyncio
from app.database import db
import logging

logging.basicConfig(level=logging.INFO)

async def check_dora_urls():
    print("--- DoraHacks Database Audit (Broad) ---")
    # Search all scholarships for anything with 'Dora' or '/bounty'
    all_docs = db.db.collection('scholarships').get()
    print(f"Total Scholarship Documents: {len(all_docs)}")
    
    broken_count = 0
    dora_count = 0
    for doc in all_docs:
        data = doc.to_dict()
        org = str(data.get('organization', '')).lower()
        url = str(data.get('source_url', ''))
        title = str(data.get('title', ''))
        
        if 'dora' in org or 'dora' in url.lower() or 'dora' in title.lower():
            dora_count += 1
            if '/bounty' in url and '/bugbounty' not in url:
                title_clean = title.encode('ascii', 'ignore').decode('ascii')
                url_clean = url.encode('ascii', 'ignore').decode('ascii')
                print(f"[BROKEN] {title_clean[:40]:<40} | {url_clean}")
                broken_count += 1
                
    print(f"--- Summary: {broken_count} broken URLs found out of {dora_count} Dora-related docs ---")

if __name__ == "__main__":
    asyncio.run(check_dora_urls())
