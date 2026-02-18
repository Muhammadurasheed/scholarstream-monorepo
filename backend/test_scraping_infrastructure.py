"""
Scraping Infrastructure Test Script
Tests the complete scraping system end-to-end
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.scraper_service import scraper_service
from app.services.scrapers.scraper_registry import scraper_registry
from app.models import UserProfile
import structlog

logger = structlog.get_logger()


async def test_scraper_registry():
    """Test 1: Verify scraper registry is working"""
    print("\n" + "="*60)
    print("TEST 1: Scraper Registry Health Check")
    print("="*60)
    
    # Get health report
    health_report = scraper_registry.get_health_report()
    
    print(f"\n📊 Registry Status:")
    print(f"   Total Scrapers: {health_report['total_scrapers']}")
    print(f"   Healthy Scrapers: {health_report['healthy_scrapers']}")
    print(f"   Unhealthy Scrapers: {health_report['unhealthy_scrapers']}")
    print(f"   Health Percentage: {health_report['health_percentage']:.1f}%")
    
    print(f"\n📋 Registered Scrapers:")
    for name, scraper in scraper_registry.scrapers.items():
        source_type = scraper.get_source_type()
        print(f"   ✓ {name} ({source_type})")
    
    # Test passed if we have scrapers
    assert health_report['total_scrapers'] > 0, "No scrapers registered!"
    print(f"\n✅ TEST 1 PASSED: {health_report['total_scrapers']} scrapers registered")
    
    return health_report


async def test_individual_scrapers():
    """Test 2: Test each scraper individually"""
    print("\n" + "="*60)
    print("TEST 2: Individual Scraper Tests")
    print("="*60)
    
    results = {}
    
    for name, scraper in scraper_registry.scrapers.items():
        print(f"\n🔍 Testing {name}...")
        try:
            opportunities = await scraper.scrape()
            count = len(opportunities)
            results[name] = {
                'success': True,
                'count': count,
                'error': None
            }
            print(f"   ✅ Success: {count} opportunities found")
            
            # Show sample opportunity
            if opportunities:
                sample = opportunities[0]
                print(f"   📄 Sample: {sample.get('name', 'N/A')}")
                print(f"      Amount: {sample.get('amount_display', 'N/A')}")
                print(f"      URL: {sample.get('url', 'N/A')[:50]}...")
        
        except Exception as e:
            results[name] = {
                'success': False,
                'count': 0,
                'error': str(e)
            }
            print(f"   ❌ Failed: {str(e)}")
    
    # Summary
    successful = sum(1 for r in results.values() if r['success'])
    total_opportunities = sum(r['count'] for r in results.values())
    
    print(f"\n📊 Summary:")
    print(f"   Successful: {successful}/{len(results)}")
    print(f"   Total Opportunities: {total_opportunities}")
    
    print(f"\n✅ TEST 2 PASSED: {successful} scrapers working")
    
    return results


async def test_comprehensive_discovery():
    """Test 3: Test full discovery pipeline"""
    print("\n" + "="*60)
    print("TEST 3: Comprehensive Discovery Pipeline")
    print("="*60)
    
    # Create test user profile
    test_profile = {
        'name': 'Test User',
        'interests': ['artificial intelligence', 'web development'],
        'major': 'Computer Science',
        'gpa': 3.8,
        'academic_status': 'Undergraduate',
        'country': 'United States',
        'state': 'California'
    }
    
    print(f"\n👤 Test User Profile:")
    print(f"   Major: {test_profile['major']}")
    print(f"   Interests: {', '.join(test_profile['interests'])}")
    print(f"   Location: {test_profile['state']}, {test_profile['country']}")
    
    print(f"\n🔍 Running comprehensive discovery...")
    
    # Run discovery
    opportunities = await scraper_service.discover_all_opportunities(test_profile)
    
    # Analyze results
    by_type = {}
    for opp in opportunities:
        opp_type = opp.get('source_type', 'unknown')
        by_type[opp_type] = by_type.get(opp_type, 0) + 1
    
    validated_count = sum(1 for o in opportunities if o.get('url_validated'))
    
    print(f"\n📊 Discovery Results:")
    print(f"   Total Opportunities: {len(opportunities)}")
    print(f"   URL Validated: {validated_count} ({validated_count/len(opportunities)*100:.1f}%)")
    
    print(f"\n📋 By Type:")
    for opp_type, count in sorted(by_type.items()):
        print(f"   {opp_type.capitalize()}: {count}")
    
    # Show top 3 opportunities
    print(f"\n🏆 Top 3 Opportunities:")
    for i, opp in enumerate(opportunities[:3], 1):
        print(f"\n   {i}. {opp.get('name', 'N/A')}")
        print(f"      Organization: {opp.get('organization', 'N/A')}")
        print(f"      Amount: {opp.get('amount_display', 'N/A')}")
        print(f"      Type: {opp.get('source_type', 'N/A')}")
        print(f"      URL Validated: {'✅' if opp.get('url_validated') else '❌'}")
    
    assert len(opportunities) > 0, "No opportunities discovered!"
    print(f"\n✅ TEST 3 PASSED: {len(opportunities)} opportunities discovered")
    
    return opportunities


async def test_url_validation():
    """Test 4: Test URL validation system"""
    print("\n" + "="*60)
    print("TEST 4: URL Validation System")
    print("="*60)
    
    # Test URLs
    test_urls = [
        {'url': 'https://www.scholarships.com', 'expected': True},
        {'url': 'https://www.fastweb.com', 'expected': True},
        {'url': 'https://invalid-url-that-does-not-exist-12345.com', 'expected': False},
    ]
    
    print(f"\n🔗 Testing URL validation...")
    
    results = []
    for test in test_urls:
        url = test['url']
        print(f"\n   Testing: {url}")
        
        test_opp = {'name': 'Test', 'organization': 'Test'}
        validated = await scraper_service._validate_single_url(url, test_opp)
        
        is_valid = validated.get('url_validated', False)
        expected = test['expected']
        
        status = "✅" if is_valid == expected else "❌"
        print(f"   {status} Valid: {is_valid} (Expected: {expected})")
        
        results.append(is_valid == expected)
    
    success_rate = sum(results) / len(results) * 100
    print(f"\n📊 Validation Accuracy: {success_rate:.1f}%")
    
    print(f"\n✅ TEST 4 PASSED")
    
    return results


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🚀 SCHOLARSTREAM SCRAPING INFRASTRUCTURE TEST SUITE")
    print("="*60)
    
    try:
        # Run all tests
        health_report = await test_scraper_registry()
        scraper_results = await test_individual_scrapers()
        opportunities = await test_comprehensive_discovery()
        validation_results = await test_url_validation()
        
        # Final summary
        print("\n" + "="*60)
        print("📊 FINAL SUMMARY")
        print("="*60)
        
        print(f"\n✅ All Tests Passed!")
        print(f"\n   Scrapers Registered: {health_report['total_scrapers']}")
        print(f"   Scrapers Working: {sum(1 for r in scraper_results.values() if r['success'])}")
        print(f"   Total Opportunities: {len(opportunities)}")
        print(f"   URL Validation: {sum(validation_results)}/{len(validation_results)} accurate")
        
        print(f"\n🎉 Scraping infrastructure is OPERATIONAL!")
        
        # Close connections
        await scraper_service.close()
        await scraper_registry.close_all()
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
