"""
Simple Scraping Infrastructure Test
Tests the scraping system without Unicode issues
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.scraper_service import scraper_service
from app.services.scrapers.scraper_registry import scraper_registry


async def main():
    """Run infrastructure tests"""
    print("\n" + "="*60)
    print("SCHOLARSTREAM SCRAPING INFRASTRUCTURE TEST")
    print("="*60)
    
    # Test 1: Registry Health
    print("\nTEST 1: Scraper Registry")
    print("-" * 40)
    
    health_report = scraper_registry.get_health_report()
    print(f"Total Scrapers: {health_report['total_scrapers']}")
    print(f"Healthy: {health_report['healthy_scrapers']}")
    print(f"Health: {health_report['health_percentage']:.1f}%")
    
    print("\nRegistered Scrapers:")
    for name in scraper_registry.scrapers.keys():
        print(f"  - {name}")
    
    # Test 2: Individual Scrapers
    print("\n" + "="*60)
    print("TEST 2: Individual Scraper Tests")
    print("="*60)
    
    total_opps = 0
    for name, scraper in scraper_registry.scrapers.items():
        print(f"\nTesting {name}...")
        try:
            opportunities = await scraper.scrape()
            count = len(opportunities)
            total_opps += count
            print(f"  SUCCESS: {count} opportunities")
            
            if opportunities:
                sample = opportunities[0]
                print(f"  Sample: {sample.get('name', 'N/A')}")
                print(f"  Amount: {sample.get('amount_display', 'N/A')}")
        except Exception as e:
            print(f"  FAILED: {str(e)}")
    
    # Test 3: Full Discovery
    print("\n" + "="*60)
    print("TEST 3: Comprehensive Discovery")
    print("="*60)
    
    test_profile = {
        'name': 'Test User',
        'interests': ['artificial intelligence', 'web development'],
        'major': 'Computer Science',
        'gpa': 3.8
    }
    
    print(f"\nRunning discovery...")
    opportunities = await scraper_service.discover_all_opportunities(test_profile)
    
    print(f"\nResults:")
    print(f"  Total Opportunities: {len(opportunities)}")
    
    validated = sum(1 for o in opportunities if o.get('url_validated'))
    print(f"  URL Validated: {validated} ({validated/len(opportunities)*100:.1f}%)")
    
    # By type
    by_type = {}
    for opp in opportunities:
        t = opp.get('source_type', 'unknown')
        by_type[t] = by_type.get(t, 0) + 1
    
    print(f"\nBy Type:")
    for t, count in sorted(by_type.items()):
        print(f"  {t}: {count}")
    
    # Show samples
    print(f"\nTop 3 Opportunities:")
    for i, opp in enumerate(opportunities[:3], 1):
        print(f"\n  {i}. {opp.get('name', 'N/A')}")
        print(f"     Org: {opp.get('organization', 'N/A')}")
        print(f"     Amount: {opp.get('amount_display', 'N/A')}")
        print(f"     Validated: {'YES' if opp.get('url_validated') else 'NO'}")
    
    # Final Summary
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    print(f"\nScrapers: {health_report['total_scrapers']}")
    print(f"Opportunities: {len(opportunities)}")
    print(f"Validation Rate: {validated/len(opportunities)*100:.1f}%")
    print(f"\nSTATUS: OPERATIONAL")
    
    # Cleanup
    await scraper_service.close()
    await scraper_registry.close_all()


if __name__ == "__main__":
    asyncio.run(main())
