import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import db

async def diagnose():
    print("=== CRITICAL DIAGNOSIS ===")
    docs = await db.get_all_scholarships()
    print(f"Total records: {len(docs)}\n")
    
    print("First 10 URLs:")
    for i, d in enumerate(docs[:10]):
        print(f"{i+1}. {d.name[:40]:40} -> {d.source_url}")
    
    print("\n=== Checking for 'img' in URLs ===")
    bad = [d for d in docs if 'img' in d.source_url.lower() or len(d.source_url) < 15]
    print(f"Found {len(bad)} corrupted URLs")
    for d in bad[:5]:
        print(f"  BAD: {d.source_url} (from {d.organization})")

if __name__ == "__main__":
    asyncio.run(diagnose())
