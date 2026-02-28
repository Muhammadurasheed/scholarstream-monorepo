import asyncio
from app.database import db

async def report():
    print("--- DoraHacks Full Report ---")
    docs = db.db.collection('scholarships').get()
    found = 0
    for d in docs:
        data = d.to_dict()
        url = str(data.get('source_url', ''))
        if 'dorahacks.io' in url:
            found += 1
            title = data.get('title', 'NO TITLE')
            # Sanitize titles for terminal output
            clean_title = title.encode('ascii', 'ignore').decode('ascii')
            print(f"[{d.id}] {clean_title:<40} | {url}")
    
    print(f"\nTotal DoraHacks-related docs found: {found}")

if __name__ == "__main__":
    asyncio.run(report())
