"""
Test All Scrapers - Verify Real Data
Run this to test if scrapers are returning actual data
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

from app.services.scrapers.scraper_registry import scraper_registry
import structlog

logger = structlog.get_logger()


async def test_all_scrapers():
    """Test all registered scrapers"""
    print("=" * 80)
    print("TESTING ALL SCRAPERS")
    print("=" * 80)
    
    results = {}
    
    for name, scraper in scraper_registry.scrapers.items():
        print(f"\n[*] Testing: {name}")
        print("-" * 80)
        
        try:
            opportunities = await scraper.scrape()
            
            results[name] = {
                'status': 'SUCCESS' if len(opportunities) > 0 else 'NO_DATA',
                'count': len(opportunities),
                'sample': opportunities[0] if opportunities else None
            }
            
            if opportunities:
                print(f"[OK] SUCCESS: Found {len(opportunities)} opportunities")
                print(f"\nSample Opportunity:")
                sample = opportunities[0]
                print(f"   Name: {sample.get('name', 'N/A')}")
                print(f"   Organization: {sample.get('organization', 'N/A')}")
                print(f"   Amount: {sample.get('amount_display', sample.get('amount', 'N/A'))}")
                print(f"   Deadline: {sample.get('deadline', 'N/A')}")
                print(f"   URL: {sample.get('url', 'N/A')[:80]}...")
            else:
                print(f"[WARN] NO DATA: Scraper returned 0 opportunities")
                
        except Exception as e:
            results[name] = {
                'status': 'ERROR',
                'error': str(e)
            }
            print(f"[ERROR] {str(e)}")
        
        # Close client
        await scraper._close_client()
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    success_count = sum(1 for r in results.values() if r['status'] == 'SUCCESS')
    no_data_count = sum(1 for r in results.values() if r['status'] == 'NO_DATA')
    error_count = sum(1 for r in results.values() if r['status'] == 'ERROR')
    total_opportunities = sum(r.get('count', 0) for r in results.values())
    
    print(f"\n[OK] Successful: {success_count}/{len(results)}")
    print(f"[WARN] No Data: {no_data_count}/{len(results)}")
    print(f"[ERROR] Errors: {error_count}/{len(results)}")
    print(f"[TOTAL] Opportunities: {total_opportunities}")
    
    print("\n" + "=" * 80)
    print("DETAILED RESULTS")
    print("=" * 80)
    
    for name, result in results.items():
        status_label = {
            'SUCCESS': '[OK]',
            'NO_DATA': '[WARN]',
            'ERROR': '[ERROR]'
        }.get(result['status'], '[?]')
        
        print(f"\n{status_label} {name}: {result['status']}")
        if result['status'] == 'SUCCESS':
            print(f"   Count: {result['count']}")
        elif result['status'] == 'ERROR':
            print(f"   Error: {result['error']}")


if __name__ == "__main__":
    asyncio.run(test_all_scrapers())
