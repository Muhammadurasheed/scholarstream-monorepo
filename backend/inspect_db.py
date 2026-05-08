
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import db

async def inspect():
    print("=== INSPECTING TARGETED SOURCES ===")
    try:
        # Fetch all
        docs = await db.get_all_scholarships()
        
        targets = [d for d in docs if 'devpost' in d.source_url or 'intigriti' in d.source_url]
        print(f"Found {len(targets)} targeted documents (DevPost/Intigriti).")
        print("Searching for 'img' in URLs...")
        # NOTE: scholarships_ref is not defined in the provided context.
        # Assuming it's meant to be db.scholarships_ref or similar.
        # For faithful reproduction, it's kept as scholarships_ref.
        for s in docs:
            url = s.source_url
            count += 1
            
            if 'img' in url or len(url) < 10:
                 print(f"BAD URL FOUND: {url} (ID: {s.id})")
                 bad_count += 1
            else:
                 if count % 20 == 0:
                     print(f"Good URL: {url}")
            
            if 'img' in url or len(url) < 10:
                 print(f"BAD URL FOUND: {url} (ID: {doc.id})")
                 bad_count += 1
            else:
                 if count % 20 == 0:
                     print(f"Good URL: {url}")

        print(f"Scanned {count} records. Found {bad_count} bad URLs.")
        print("-" * 20)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(inspect())
