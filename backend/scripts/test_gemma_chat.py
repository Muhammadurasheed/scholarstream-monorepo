import asyncio
import structlog
from app.services.chat_service import chat_service

async def test_gemma_chat():
    print("Testing Gemma 4 Chat Agent...")
    user_id = "demo_guest_user"
    message = "I am a CS student looking for scholarships in Nigeria. Any grants for fees?"
    context = {
        "user_profile": {
            "name": "Musa Ibrahim",
            "major": "Computer Science",
            "gpa": 3.85,
            "interests": ["AI", "Open Source"]
        }
    }
    
    try:
        response = await chat_service.chat(user_id, message, context)
        print("\n--- GEMMA 4 RESPONSE ---")
        print(f"Thinking Process: {response.get('thinking_process')}")
        print(f"Text: {response.get('text')}")
        print("------------------------\n")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_gemma_chat())
