import asyncio
import sys
from pathlib import Path
import httpx

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

async def debug_devpost():
    url = "https://devpost.com/hackathons?status[]=open&order=submission_period"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://devpost.com/'
    }
    
    print(f"Fetching {url}...")
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(url, headers=headers)
        
    print(f"Status: {response.status_code}")
    print(f"URL: {response.url}")
    print(f"Content length: {len(response.text)}")
    
    with open("devpost_debug.html", "w", encoding="utf-8") as f:
        f.write(response.text)
    
    if "challenge-listing" in response.text:
        print("Found 'challenge-listing' class")
    else:
        print("Did NOT find 'challenge-listing' class")
        
    if "flex-row tile-anchor" in response.text:
         print("Found 'flex-row tile-anchor' class")
    else:
         print("Did NOT find 'flex-row tile-anchor' class")

if __name__ == "__main__":
    asyncio.run(debug_devpost())
