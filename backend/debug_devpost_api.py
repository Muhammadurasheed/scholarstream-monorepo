import asyncio
import sys
from pathlib import Path
import httpx
import json

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

async def debug_devpost_api():
    # Trying the API endpoint found in the HTML source
    url = "https://devpost.com/api/hackathons"
    
    # Also try parameters that might be needed
    params = {
        'status[]': 'open',
        'order': 'submission_period',
        'page': 1
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
         'Accept': 'application/json, text/javascript, */*; q=0.01',
    }
    
    print(f"Fetching {url} with params {params}...")
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(url, params=params, headers=headers)
        
    print(f"Status: {response.status_code}")
    print(f"URL: {response.url}")
    
    try:
        data = response.json()
        print(f"Response Type: {type(data)}")
        if isinstance(data, list):
            print(f"Found {len(data)} items")
            if data:
                print(f"Sample: {data[0].keys()}")
        elif isinstance(data, dict):
             print(f"Keys: {data.keys()}")
             if 'hackathons' in data:
                 print(f"Found {len(data['hackathons'])} hackathons")
    except Exception as e:
        print(f"Failed to parse JSON: {e}")
        print(f"Text content: {response.text[:500]}")

if __name__ == "__main__":
    asyncio.run(debug_devpost_api())
