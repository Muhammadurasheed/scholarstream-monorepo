import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import db

async def check_current_state():
    print("=== CHECKING CURRENT DATABASE STATE ===")
    docs = await db.get_all_scholarships()
    print(f"Total records: {len(docs)}\n")
    
    print("First 20 URLs (with source type):")
    for i, d in enumerate(docs[:20]):
        print(f"{i+1}. [{d.source_type:12}] {d.name[:35]:35} -> {d.source_url}")
    
    print("\n=== Checking DevPost URLs specifically ===")
    devpost = [d for d in docs if 'devpost' in d.source_url.lower()]
    print(f"Found {len(devpost)} DevPost records")
    for d in devpost[:5]:
        print(f"  {d.source_url}")
    
    print("\n=== Checking for broken URLs ===")
    broken = [d for d in docs if 'img' in d.source_url.lower() or len(d.source_url) < 15 or 'hackathons/' in d.source_url]
    print(f"Found {len(broken)} potentially broken URLs")
    for d in broken[:10]:
        print(f"  BROKEN: {d.source_url} (from {d.organization})")

if __name__ == "__main__":
    asyncio.run(check_current_state())
