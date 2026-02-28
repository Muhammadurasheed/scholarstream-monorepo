import asyncio
from app.database import db

async def inspect():
    print("--- Web3Go Grant Inspection ---")
    docs = db.db.collection('scholarships').where('title', '==', 'Web3Go Grant').get()
    if not docs:
        # Try search by organization
        docs = db.db.collection('scholarships').where('organization', '==', 'Web3Go').get()
    
    if docs:
        print(f"Found {len(docs)} docs.")
        for d in docs:
            print(f"ID: {d.id}")
            data = d.to_dict()
            for k, v in data.items():
                print(f"  {k}: {v}")
    else:
        print("Not found by title or org.")

if __name__ == "__main__":
    asyncio.run(inspect())
