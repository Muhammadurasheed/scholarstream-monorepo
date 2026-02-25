
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.scrapers.hackathons.devpost_api_scraper import populate_database_with_devpost
from app.services.scrapers.hackathons.unstop_scraper import populate_database_with_unstop
from app.services.scrapers.hackathons.devpost_deep_scraper import populate_database_with_devpost_deep
from app.services.scrapers.bounties.intigriti_scraper import populate_database_with_intigriti
from app.services.scrapers.hackathons.hackquest_scraper import populate_database_with_hackquest
from app.services.scrapers.hackathons.taikai_scraper import populate_database_with_taikai
from app.services.scrapers.bounties.multi_platform_scraper import populate_database_multi_platform
from app.services.crawler_service import crawler_service

async def populate_all():
    print("=== STARTING DATABASE REPOPULATION ===")
    
    # 1. DevPost
    print("\n[1/7] Populating DevPost (API)...")
    try:
        count = await populate_database_with_devpost()
        print(f"      -> Added {count} items.")
    except Exception as e:
        print(f"      -> Failed: {e}")

    # 1b. DevPost Deep
    print("\n[2/7] Populating DevPost (Deep)...")
    try:
        count = await populate_database_with_devpost_deep()
        print(f"      -> Added {count} items.")
    except Exception as e:
        print(f"      -> Failed: {e}")

    # 1c. Unstop
    print("\n[3/7] Populating Unstop (Deep)...")
    try:
        count = await populate_database_with_unstop()
        print(f"      -> Added {count} items.")
    except Exception as e:
        print(f"      -> Failed: {e}")

    # 2. Intigriti
    print("\n[2/5] Populating Intigriti...")
    try:
        count = await populate_database_with_intigriti()
        print(f"      -> Added {count} items.")
    except Exception as e:
        print(f"      -> Failed: {e}")
        
    # 3. HackQuest
    print("\n[3/5] Populating HackQuest...")
    try:
        count = await populate_database_with_hackquest()
        print(f"      -> Added {count} items.")
    except Exception as e:
        print(f"      -> Failed: {e}")
        
    # 4. Taikai
    print("\n[4/5] Populating Taikai...")
    try:
        count = await populate_database_with_taikai()
        print(f"      -> Added {count} items.")
    except Exception as e:
        print(f"      -> Failed: {e}")
        
    # 7. Multi-Platform
    print("\n[7/7] Populating Multi-Platform (DoraHacks, Gitcoin, etc.)...")
    try:
        results, scholarships = await populate_database_multi_platform() # Fix: multi_platform returns tuple in newest version
        saved_count = results.get('saved', 0)
        print(f"      -> Added {saved_count} items (breakdown: {results})")
    except Exception as e:
        print(f"      -> Failed: {e}")

    print("\n=== REPOPULATION COMPLETE ===")
    await crawler_service.close()

if __name__ == "__main__":
    asyncio.run(populate_all())
