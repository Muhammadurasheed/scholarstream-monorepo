import httpx
import asyncio

async def test_dora():
    urls = [
        "https://dorahacks.io/api/bugbounty/list?status=open&page=1&limit=5",
        "https://dorahacks.io/api/bounties/list?status=open&page=1&limit=5",
        "https://dorahacks.io/api/v1/bugbounty/list?status=open&page=1&limit=5"
    ]
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    async with httpx.AsyncClient() as client:
        for url in urls:
            try:
                print(f"Testing {url}...")
                resp = await client.get(url, headers=headers)
                print(f"Status: {resp.status_code}")
                if resp.status_code == 200:
                    print(f"Success! Data received from {url}")
                    # print(resp.text[:500])
                    break
                else:
                    print(f"Failed: {resp.text[:100]}")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_dora())
