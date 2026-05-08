
import asyncio
import json
import sys
import os

# Improve path handling
sys.path.append(os.getcwd())

from app.services.crawler_service import crawler_service

async def debug():
    url = "https://earn.superteam.fun/api/listings?type=bounty&status=open"
    # url = "https://dorahacks.io/api/hackathon?page=1&page_size=5&status=active"
    print(f"Fetching {url}...")
    content = await crawler_service.fetch_content(url)
    
    with open("superteam_debug.html", "w", encoding="utf-8") as f:
        f.write(content)
    print("Saved content to superteam_debug.html")

    # Try to parse
    import re
    pre_match = re.search(r'<pre[^>]*>(.*?)</pre>', content, re.DOTALL)
    if pre_match:
        json_text = pre_match.group(1)
        print("Found JSON in PRE tag.")
        try:
            data = json.loads(json_text)
            print("Parsed JSON keys:", data.keys())
            if 'results' in data:
                print("First item keys:", data['results'][0].keys())
        except Exception as e:
            print("JSON parse error:", e)
    else:
        print("No PRE tag found. Raw content usually implies full HTML.")

if __name__ == "__main__":
    asyncio.run(debug())
