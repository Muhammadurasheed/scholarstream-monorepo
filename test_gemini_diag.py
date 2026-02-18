
import asyncio
import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai

# Load backend .env
load_dotenv('backend/.env')

async def test_gemini():
    api_key = os.getenv('GEMINI_API_KEY')
    model_name = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
    
    print(f"API Key found: {'Yes' if api_key else 'No'}")
    print(f"Using model: {model_name}")
    
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in .env")
        return

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        
        print("Attempting to generate content...")
        response = await model.generate_content_async("Hello, are you online?")
        print(f"Response success: {response.text[:50]}...")
        
    except Exception as e:
        print(f"ERROR: Gemini call failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_gemini())
