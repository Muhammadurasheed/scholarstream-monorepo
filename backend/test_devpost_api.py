import httpx
import asyncio
import json

async def test_devpost_api():
    print("=== Testing DevPost API ===")
    url = "https://devpost.com/api/hackathons"
    params = {
        'status[]': 'open',
        'page': 1,
        'per_page': 2
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params, headers=headers)
        data = response.json()
        
        print(f"Status: {response.status_code}")
        print(f"Total hackathons: {len(data.get('hackathons', []))}\n")
        
        for i, h in enumerate(data.get('hackathons', [])[:2]):
            print(f"\n--- Hackathon {i+1} ---")
            print(f"Title: {h.get('title')}")
            print(f"URL: {h.get('url')}")
            print(f"Organization: {h.get('organization_name')}")
            print(f"Prize: {h.get('prize_amount')}")
            print(f"\nFull keys: {list(h.keys())}")

if __name__ == "__main__":
    asyncio.run(test_devpost_api())
