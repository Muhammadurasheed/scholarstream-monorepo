import httpx
import asyncio
import re
import json

async def extract_data():
    url = "https://dorahacks.io/bugbounty"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                html = resp.text
                match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
                if match:
                    data = json.loads(match.group(1))
                    # print(json.dumps(data, indent=2)[:2000])
                    
                    # Search for bounty list
                    def find_key(obj, key_to_find):
                        if isinstance(obj, dict):
                            if key_to_find in obj:
                                return obj[key_to_find]
                            for v in obj.values():
                                res = find_key(v, key_to_find)
                                if res: return res
                        elif isinstance(obj, list):
                            for item in obj:
                                res = find_key(item, key_to_find)
                                if res: return res
                        return None
                    
                    bounties = find_key(data, 'bounties') or find_key(data, 'list') or find_key(data, 'items')
                    if bounties:
                        print("Found bounties in __NEXT_DATA__!")
                        print(json.dumps(bounties, indent=2)[:2000])
                    else:
                        print("Could not find bounties in __NEXT_DATA__")
                else:
                    print("__NEXT_DATA__ not found")
            else:
                print(f"Failed: {resp.status_code}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(extract_data())
