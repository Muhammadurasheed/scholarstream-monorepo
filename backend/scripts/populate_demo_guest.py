"""
ScholarStream: Demo Persona Initializer
Injects a high-quality 'Musa' profile for frictionless judge evaluation.
"""
import asyncio
import firebase_admin
from firebase_admin import credentials, firestore
from app.config import settings

async def populate_demo_guest():
    print("🚀 Initializing Demo Persona...")
    
    # Initialize Firebase if not already done
    if not firebase_admin._apps:
        cred = credentials.Certificate(settings.firebase_credentials)
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()
    guest_uid = settings.guest_uid
    
    demo_profile = {
        "uid": guest_uid,
        "name": "Musa Ibrahim",
        "email": "musa.demo@scholarstream.app",
        "bio": "3rd-year Computer Science student at University of Lagos. Passionate about AI for social good and building low-bandwidth educational tools for rural communities.",
        "academic_status": "Undergraduate",
        "major": "Computer Science",
        "school": "University of Lagos",
        "year": "Junior (Year 3)",
        "gpa": "3.85",
        "interests": ["Artificial Intelligence", "Sustainability", "FinTech", "Education"],
        "skills": ["Python", "React", "FastAPI", "Data Analysis", "Cloud Computing"],
        "citizenship": "Nigeria",
        "ethnicity": "African",
        "gender": "Male",
        "linkedin_url": "https://linkedin.com/in/musa-demo",
        "github_url": "https://github.com/musa-demo",
        "projects": [
            {
                "title": "EcoTrack IoT",
                "description": "A low-cost IoT sensor network for monitoring water quality in urban slums.",
                "tech_stack": "Python, Raspberry Pi, LoRaWAN",
                "role": "Lead Developer"
            }
        ],
        "essays": {
            "personal_statement": "Growing up in a community with limited resources, I saw how technology could bridge the gap. My goal is to build AI that doesn't just work for the elite, but empowers the everyday student.",
            "career_goals": "I aim to become a Senior AI Researcher focusing on Edge Intelligence for the Global South.",
            "community_impact": "I volunteer as a coding mentor for 'Tech4All', teaching basics to out-of-school youth."
        },
        "created_at": firestore.SERVER_TIMESTAMP,
        "is_demo": True
    }
    
    # Save to Firestore
    db.collection('users').document(guest_uid).set(demo_profile)
    print(f"✅ Demo Persona 'Musa' injected successfully (UID: {guest_uid})")

if __name__ == "__main__":
    asyncio.run(populate_demo_guest())
