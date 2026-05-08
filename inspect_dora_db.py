from app.database import db
import asyncio

async def check_dora():
    docs = db.collection('scholarships').where('organization', '==', 'DoraHacks').limit(10).get()
    for doc in docs:
        data = doc.to_dict()
        print(f"ID: {doc.id}")
        print(f"Title: {data.get('title')}")
        print(f"URL: {data.get('source_url')}")
        print("-" * 20)

if __name__ == "__main__":
    asyncio.run(check_dora())
