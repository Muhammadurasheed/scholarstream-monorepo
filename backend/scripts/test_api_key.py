import os
import httpx
from app.config import settings

def test_gemma_api_key():
    api_key = settings.gemini_api_key
    project_id = "scholarstream-gemma4good"
    endpoint = f"https://aiplatform.googleapis.com/v1/projects/{project_id}/locations/global/endpoints/openapi/chat/completions?key={api_key}"
    
    payload = {
        "model": "google/gemma-4-26b-a4b-it-maas",
        "messages": [{"role": "user", "content": "What's the weather in Lagos?"}],
        "stream": False,
        "tools": [{
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"}
                    }
                }
            }
        }],
        "tool_choice": "auto"
    }
    
    headers = {"Content-Type": "application/json"}
    
    print(f"Testing Gemma API Key on project: {project_id}...")
    try:
        response = httpx.post(endpoint, json=payload, headers=headers, timeout=30.0)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_gemma_api_key()
