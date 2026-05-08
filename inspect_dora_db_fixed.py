import sys
import os

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.database import db
import asyncio

async def check_dora():
    docs = db.collection('scholarships').where('organization', '==', 'DoraHacks').limit(10).get()
    if not docs:
        print("No DoraHacks documents found in DB")
        return
        
    for doc in docs:
        data = doc.to_dict()
        print(f"ID: {doc.id}")
        print(f"Title: {data.get('title')}")
        print(f"URL: {data.get('source_url')}")
        print("-" * 20)

if __name__ == "__main__":
    asyncio.run(check_dora())
