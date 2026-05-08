
import asyncio
import sys
import os

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.scrapers.hackathons.devpost_api_scraper import scrape_devpost_api
from app.services.scrapers.bounties.intigriti_scraper import scrape_intigriti_programs
from app.services.scrapers.hackathons.hackquest_scraper import scrape_hackquest_events
from app.services.scrapers.hackathons.taikai_scraper import scrape_taikai_events
from app.services.scrapers.bounties.multi_platform_scraper import scrape_all_platforms
from app.services.crawler_service import crawler_service

async def verify_scraper(name, scraper_func, is_tuple_return=False):
    print(f"\n[TEST] Starting {name}...")
    try:
        if is_tuple_return:
            results, scholarships = await scraper_func()
        else:
            scholarships = await scraper_func()
            
        print(f"[PASS] {name} found {len(scholarships)} items.")
        
        if len(scholarships) > 0:
            s = scholarships[0]
            print(f"   -> Sample: {s.name}")
            print(f"      URL: {s.source_url}")
            print(f"      Amount: {s.amount_display}")
            print(f"      Deadline: {s.deadline} (Timestamp: {s.deadline_timestamp})")
            
            # Check for critical fixes
            if name == "Intigriti":
                if s.deadline is None:
                    print(f"      [VERIFIED] Intigriti deadline is None (Ongoing) - Fix Confirmed")
                elif s.deadline_timestamp == 0:
                     print(f"      [FAIL] Intigriti deadline is 0 (1970 Issue Persists)")
            
            if name == "HackQuest":
                if "hackquest.io" in s.source_url:
                     print(f"      [VERIFIED] HackQuest URL looks valid")

            if name == "DevPost":
                if "devpost.com" in s.source_url and not "canonical" in s.source_url: # rough check
                     print(f"      [VERIFIED] DevPost URL: {s.source_url}")

        else:
            print(f"[WARN] {name} returned 0 items. Possible block or empty feed.")
            
    except Exception as e:
        print(f"[FAIL] {name} crashed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    print("=== STARTING SCRAPER VERIFICATION ===")
    
    # 1. DevPost
    await verify_scraper("DevPost", lambda: scrape_devpost_api(max_pages=1))
    
    # 2. Intigriti (Playwright)
    await verify_scraper("Intigriti", scrape_intigriti_programs)
    
    # 3. HackQuest (Playwright GraphQL)
    await verify_scraper("HackQuest", scrape_hackquest_events)
    
    # 4. Taikai (Playwright)
    await verify_scraper("Taikai", scrape_taikai_events)
    
    # 5. Multi-Platform (DoraHacks, Gitcoin, etc.)
    await verify_scraper("Multi-Platform", scrape_all_platforms, is_tuple_return=True)
    
    print("\n=== VERIFICATION COMPLETE ===")
    
    # Cleanup
    await crawler_service.close()

if __name__ == "__main__":
    asyncio.run(main())
