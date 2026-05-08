"""
DevPost API Scraper V1
Uses DevPost's public API to fetch active hackathons reliably.
This is more stable than HTML scraping since it returns structured JSON.
"""
import httpx
import asyncio
import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.flink_processor import generate_opportunity_id
from app.database import db
from app.models import Scholarship

logger = structlog.get_logger()

# DevPost API endpoint for hackathons
DEVPOST_API_URL = "https://devpost.com/api/hackathons"

# User agent to mimic browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://devpost.com/hackathons',
    'X-Requested-With': 'XMLHttpRequest',
}


async def fetch_devpost_hackathons(
    status: str = "open",
    order: str = "submission_period",
    page: int = 1,
    per_page: int = 100
) -> List[Dict[str, Any]]:
    """
    Fetch hackathons from DevPost API.
    
    Args:
        status: 'open', 'upcoming', 'ended'
        order: 'submission_period', 'prize_amount', 'recently_added'
        page: Page number for pagination
        per_page: Results per page (max 100)
        
    Returns:
        List of hackathon data dictionaries
    """
    params = {
        'status[]': status,
        'order': order,
        'page': page,
        'per_page': per_page
    }
    
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(DEVPOST_API_URL, params=params, headers=HEADERS)
            
            if response.status_code == 200:
                data = response.json()
                hackathons = data.get('hackathons', []) if isinstance(data, dict) else data
                logger.info("DevPost API success", status=status, count=len(hackathons))
                return hackathons
            else:
                logger.warning("DevPost API error", status_code=response.status_code)
                return []
    except Exception as e:
        logger.error("DevPost API fetch failed", error=str(e))
        return []


def transform_to_scholarship(hackathon: Dict[str, Any]) -> Optional[Scholarship]:
    """
    Transform DevPost API hackathon data to Scholarship model.
    """
    try:
        # Extract core fields
        title = hackathon.get('title', '')
        url = hackathon.get('url', '')
        
        if not title or not url:
            return None
            
        # Fix: Trust the API provided URL.
        # The previous logic attempted to rewrite subdomains which caused 404s for many hackathons.
        # We only clean tracking parameters if necessary, but DevPost API URLs are generally clean.
        
        # Parse prize amount
        prize_str = hackathon.get('prize_amount', '$0')
        amount = 0
        if prize_str:
            # Clean HTML tags if present (e.g. <span data-currency-value>75,000</span>)
            import re
            prize_clean = re.sub(r'<[^>]+>', '', str(prize_str))
            
            # Remove currency symbols and parse
            amount_str = ''.join(c for c in prize_clean if c.isdigit() or c == '.')
            try:
                amount = int(float(amount_str)) if amount_str else 0
            except ValueError:
                amount = 0
        
        # Parse deadline
        deadline = None
        deadline_timestamp = None
        submission_period = hackathon.get('submission_period', {})
        
        if submission_period:
            end_date = submission_period.get('ends_at')
            if end_date:
                try:
                    deadline_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    deadline = deadline_dt.strftime('%Y-%m-%d')
                    deadline_timestamp = int(deadline_dt.timestamp())
                    
                    # Skip if already expired
                    if deadline_dt < datetime.now(deadline_dt.tzinfo):
                        logger.debug("Skipping expired hackathon", title=title[:30])
                        return None
                except Exception:
                    pass
        
        # CRITICAL FIX: DevPost API returns URLs in SUBDOMAIN format already
        # Example: https://ai-partner-catalyst.devpost.com/
        # NO transformation needed - the API provides the correct, working URL
        # Previous logic was looking for devpost.com/hackathons/slug which doesn't exist
        
        # Just use the URL as-is from the API
        # It's already in the correct subdomain format
        
        opportunity_data = {
            'id': '',  # Will be generated
            'name': title,
            'title': title,
            'organization': hackathon.get('organization_name', 'DevPost'),
            'amount': amount,
            'amount_display': hackathon.get('prize_amount', 'Varies'),
            'deadline': deadline,
            'deadline_timestamp': deadline_timestamp,
            'source_url': url,
            'description': hackathon.get('tagline', '') or hackathon.get('displayed_location', {}).get('location', ''),
            # CRITICAL FIX: themes are objects {'id': X, 'name': 'ThemeName'}, extract just the name
            'tags': ['Hackathon', 'DevPost'] + [
                theme.get('name') if isinstance(theme, dict) else str(theme)
                for theme in (hackathon.get('themes', []) or [])[:5]
                if theme
            ],
            'geo_tags': ['Global', 'Online'] if hackathon.get('open_state') == 'open' else [],
            'type_tags': ['Hackathon'],
            'eligibility': {
                'gpa_min': None,
                'majors': [],
                'states': [],
                'citizenship': 'any',
                'grade_levels': []
            },
            'eligibility_text': f"Open to participants. Submissions: {hackathon.get('submissions_count', 0)}",
            'source_type': 'devpost',
            'match_score': 50,  # Default, will be personalized later
            'match_tier': 'Good',
            'verified': True,
            'last_verified': datetime.now().isoformat(),
            'priority_level': 'HIGH' if amount >= 10000 else 'MEDIUM'
        }
        
        # Generate stable ID
        opportunity_data['id'] = generate_opportunity_id(opportunity_data)
        
        return Scholarship(**opportunity_data)
        
    except Exception as e:
        logger.warning("Failed to transform hackathon", error=str(e), title=hackathon.get('title', 'Unknown'))
        return None


async def scrape_devpost_api(max_pages: int = 3) -> List[Scholarship]:
    """
    Main function to scrape DevPost hackathons via API.
    
    Args:
        max_pages: Maximum number of pages to fetch (each page has ~100 results)
        
    Returns:
        List of Scholarship objects
    """
    logger.info("Starting DevPost API scrape", max_pages=max_pages)
    
    all_scholarships = []
    
    # Fetch open hackathons
    for page in range(1, max_pages + 1):
        hackathons = await fetch_devpost_hackathons(status="open", page=page)
        
        if not hackathons:
            break
            
        for hackathon in hackathons:
            scholarship = transform_to_scholarship(hackathon)
            if scholarship:
                all_scholarships.append(scholarship)
        
        # Small delay between pages to be nice
        await asyncio.sleep(0.5)
    
    # Also fetch upcoming hackathons (first page only)
    upcoming = await fetch_devpost_hackathons(status="upcoming", page=1, per_page=50)
    for hackathon in upcoming:
        scholarship = transform_to_scholarship(hackathon)
        if scholarship:
            all_scholarships.append(scholarship)
    
    logger.info("DevPost API scrape complete", total_hackathons=len(all_scholarships))
    return all_scholarships


async def populate_database_with_devpost() -> int:
    """
    Scrape DevPost and save to Firestore.
    Returns the number of opportunities saved.
    """
    logger.info("Populating database with DevPost hackathons...")
    
    scholarships = await scrape_devpost_api(max_pages=3)
    
    saved_count = 0
    for scholarship in scholarships:
        try:
            await db.save_scholarship(scholarship)
            saved_count += 1
        except Exception as e:
            logger.warning("Failed to save scholarship", id=scholarship.id, error=str(e))
            continue
    
    logger.info("DevPost population complete", saved=saved_count, total=len(scholarships))
    return saved_count


# CLI usage
if __name__ == "__main__":
    async def main():
        scholarships = await scrape_devpost_api()
        print(f"\nFound {len(scholarships)} hackathons:")
        for s in scholarships[:10]:
            print(f"  - {s.name}: {s.amount_display} (deadline: {s.deadline})")
            print(f"    URL: {s.source_url}")
    
    asyncio.run(main())
