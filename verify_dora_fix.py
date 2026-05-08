import asyncio
from app.database import db

async def verify():
    # Check specifically for Web3Go Grant
    docs = db.db.collection('scholarships').where('title', '==', 'Web3Go Grant').get()
    if docs:
        url = docs[0].to_dict().get('source_url')
        print(f"VERIFIED Web3Go Grant URL: {url}")
    else:
        print("Web3Go Grant NOT FOUND")

if __name__ == "__main__":
    asyncio.run(verify())
