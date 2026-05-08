"""
Quick Scraper Test - Test individual scrapers
"""
import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

from app.services.scrapers.kaggle_scraper import KaggleScraper
from app.services.scrapers.devpost_scraper import DevpostScraper
from app.services.scrapers.web3_bounties_scraper import Web3BountiesScraper


async def test_kaggle():
    print("\n" + "="*80)
    print("TESTING KAGGLE SCRAPER")
    print("="*80)
    
    scraper = KaggleScraper()
    opportunities = await scraper.scrape()
    await scraper._close_client()
    
    print(f"\n[RESULT] Found {len(opportunities)} competitions")
    if opportunities:
        print(f"\nSample:")
        sample = opportunities[0]
        print(f"  Name: {sample.get('name')}")
        print(f"  Amount: {sample.get('amount_display')}")
        print(f"  Deadline: {sample.get('deadline')}")
        print(f"  URL: {sample.get('url')}")


async def test_devpost():
    print("\n" + "="*80)
    print("TESTING DEVPOST SCRAPER")
    print("="*80)
    
    scraper = DevpostScraper()
    opportunities = await scraper.scrape()
    await scraper._close_client()
    
    print(f"\n[RESULT] Found {len(opportunities)} hackathons")
    if opportunities:
        print(f"\nSample:")
        sample = opportunities[0]
        print(f"  Name: {sample.get('name')}")
        print(f"  Organization: {sample.get('organization')}")
        print(f"  Amount: {sample.get('amount_display')}")
        print(f"  URL: {sample.get('url')}")


async def test_web3():
    print("\n" + "="*80)
    print("TESTING WEB3 BOUNTIES SCRAPER")
    print("="*80)
    
    scraper = Web3BountiesScraper()
    opportunities = await scraper.scrape()
    await scraper._close_client()
    
    print(f"\n[RESULT] Found {len(opportunities)} bounties")
    if opportunities:
        print(f"\nSample:")
        sample = opportunities[0]
        print(f"  Name: {sample.get('name')}")
        print(f"  Organization: {sample.get('organization')}")
        print(f"  Amount: {sample.get('amount_display')}")
        print(f"  URL: {sample.get('url')}")


async def main():
    await test_kaggle()
    await test_devpost()
    await test_web3()


if __name__ == "__main__":
    asyncio.run(main())
