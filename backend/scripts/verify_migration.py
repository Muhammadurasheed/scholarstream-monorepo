import asyncio
from app.config import settings
import firebase_admin
from firebase_admin import credentials, firestore

async def verify():
    if not firebase_admin._apps:
        cred = credentials.Certificate(settings.firebase_credentials)
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()
    doc = db.collection('users').document('demo_guest_user').get()
    if doc.exists:
        print(f"✅ VERIFIED: Musa Ibrahim is in the database! (Name: {doc.to_dict()['name']})")
    else:
        print("❌ ERROR: Musa not found.")

if __name__ == "__main__":
    asyncio.run(verify())
