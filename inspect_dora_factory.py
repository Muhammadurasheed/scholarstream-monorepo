import asyncio
from app.database import db

async def inspect():
    print("--- Dora Factory Grant Inspection ---")
    docs = db.db.collection('scholarships').where('title', '==', 'Dora Factory Grant').get()
    
    if docs:
        print(f"Found {len(docs)} docs.")
        for d in docs:
            print(f"ID: {d.id}")
            data = d.to_dict()
            print(f"  source_url: {data.get('source_url')}")
    else:
        print("Dora Factory Grant NOT FOUND")

if __name__ == "__main__":
    asyncio.run(inspect())
