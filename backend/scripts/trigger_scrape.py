import asyncio
import sys
import os

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.scrapers.devpost_scraper import DevpostScraper
from app.services.flink_processor import CortexFlinkProcessor
from app.database import db
import structlog

logger = structlog.get_logger()

async def manual_scrape():
    """
    Manually run the Devpost scraper and process results through Flink.
    """
    print("STARTING MANUAL SCRAPE: Devpost")
    
    scraper = DevpostScraper()
    processor = CortexFlinkProcessor()
    
    # 1. Scrape
    print("   -> Scraping Devpost API...")
    opportunities = await scraper.scrape()
    print(f"Scraped {len(opportunities)} items.")
    
    # 2. Process (Deduplicate & Enrich)
    print("   -> Processing through Cortex (Flink)...")
    processed_count = 0
    
    for opp in opportunities:
        # Simulate Kafka stream by passing dict directly to processor
        # Note: In prod this goes via Kafka, but we call the internal logic to force DB save
        
        # We need to manually convert to Enriched format or simulate the pipeline
        # Actually, simpler: Use the processor's _process_window logic if accessible, 
        # or just save directly to DB Using the same logic as flink_processor
        
        # Let's use the actual Flink Processor logic if possible.
        # But flink_processor usually reads from Kafka.
        # Let's look at flink_processor.py... it enriches and produces to KAFKA ENRICHED TOPIC.
        # Then websocket.py reads from ENRICHED TOPIC and saves to DB.
        
        # To make this fast and bypass Kafka latency for this "Hotfix":
        # We will scrape -> convert -> save directly to DB.
        
        # Reuse devpost_scraper output which IS the raw dict.
        # Enriched format is almost same as scraped format in our simple pipeline.
        
        # Transform Data for Schema Compatibility
        import hashlib
        
        # 1. Generate ID
        url = opp.get('url') or opp.get('source_url') or 'unknown'
        opp['id'] = hashlib.md5(url.encode('utf-8')).hexdigest()
        opp['source_url'] = url
        
        # 2. Flatten Tags (Devpost returns [{'id':1, 'name':'foo'}])
        raw_tags = opp.get('tags', [])
        flat_tags = []
        for t in raw_tags:
            if isinstance(t, dict):
                flat_tags.append(t.get('name', ''))
            elif isinstance(t, str):
                flat_tags.append(t)
        opp['tags'] = flat_tags
        
        # 3. Fix Citizenship (Schema expects str, might get list)
        eligibility = opp.get('eligibility', {})
        if isinstance(eligibility, dict):
            cit = eligibility.get('citizenship')
            if isinstance(cit, list):
                eligibility['citizenship'] = cit[0] if cit else 'Any'
            opp['eligibility'] = eligibility
            
        # 4. Ensure name field
        if 'name' not in opp and 'title' in opp:
            opp['name'] = opp['title']

        # Save to DB
        from app.models import Scholarship
        try:
            # Quick Map
            s = Scholarship(**opp)
            await db.save_scholarship(s)
            processed_count += 1
            # Encode/Decode to safe ascii for Windows console
            safe_title = s.name.encode('ascii', 'ignore').decode('ascii')
            print(f"      + Saved: {safe_title}")
        except Exception as e:
            safe_error = str(e).encode('ascii', 'ignore').decode('ascii')
            print(f"      x Failed to save item: {safe_error}")

    print(f"Scrape & Import Complete. {processed_count} scholarships added to database.")

if __name__ == "__main__":
    asyncio.run(manual_scrape())
