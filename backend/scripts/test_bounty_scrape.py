
import asyncio
import sys
import os
import structlog
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.crawler_service import crawler_service
from app.services.ai_enrichment_service import ai_enrichment_service

# Configure logger
from structlog.dev import ConsoleRenderer
structlog.configure(processors=[ConsoleRenderer()])
logger = structlog.get_logger()

async def test_bounty_extraction():
    url = "https://dorahacks.io/hackathon" 
    print(f"=== TESTING BOUNTY EXTRACTION FROM: {url} ===")
    
    # 1. Crawl (Simulate Hunter Drone)
    print("Deploying Hunter Drone...")
    # Manually use Playwright to get content to avoid full Kafka pipeline for test
    await crawler_service._init_browser()
    context = await crawler_service._create_stealth_context()
    page = await context.new_page()
    
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        # Wait for hydration
        await asyncio.sleep(5) 
        # Scroll for lazy load
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
        await asyncio.sleep(2)
        
        html = await page.content()
        print(f"✅ Crawl Successful. HTML Size: {len(html)} chars")
        
        # 2. Extract (Simulate AI Refinery)
        print("Sending to AI Refinery...")
        opportunities = await ai_enrichment_service.extract_opportunities_from_html(html, url)
        
        print(f"\n✅ AI Extraction Result: {len(opportunities)} opportunities found")
        for opp in opportunities:
            print(f"- [{opp.get('type', 'UNKNOWN').upper()}] {opp.get('title')} ({opp.get('amount_display')})")
            print(f"  Source: {opp.get('url')}")
            
    except Exception as e:
        print(f"❌ Test Failed: {e}")
    finally:
        await crawler_service.close()

if __name__ == "__main__":
    asyncio.run(test_bounty_extraction())
