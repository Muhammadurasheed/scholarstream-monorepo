"""
TAIKAI Hackathon Scraper - ENHANCED PLAYWRIGHT EDITION
Fetches hackathons from taikai.network using robust Playwright-based fetching.

Bismillah - Built for maximum reliability with multiple extraction strategies.
"""
import json
import re
import structlog
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.flink_processor import generate_opportunity_id
from app.database import db
from app.models import Scholarship
from app.services.crawler_service import crawler_service

logger = structlog.get_logger()

# TAIKAI URLs to scrape
TAIKAI_URLS = [
    "https://taikai.network/hackathons",
    "https://taikai.network/en/hackathons",
]

# TAIKAI GraphQL API endpoint (if available)
TAIKAI_API_URL = "https://api.taikai.network/graphql"


async def fetch_taikai_events() -> List[Dict[str, Any]]:
    """
    Fetch TAIKAI hackathons using multiple strategies.
    Strategy 1: GraphQL API
    Strategy 2: Playwright + __NEXT_DATA__
    Strategy 3: Playwright + Apollo State
    Strategy 4: HTML scraping
    """
    all_events = []
    
    # Strategy 1: Try GraphQL API first (fastest if it works)
    try:
        api_events = await fetch_taikai_graphql()
        if api_events:
            logger.info("TAIKAI GraphQL API success", count=len(api_events))
            return api_events
    except Exception as e:
        logger.debug("TAIKAI GraphQL failed, trying Playwright", error=str(e))
    
    # Strategy 2-4: Playwright-based scraping
    for url in TAIKAI_URLS:
        try:
            logger.info("Fetching TAIKAI via Playwright", url=url)
            html = await crawler_service.fetch_content(url)
            
            if not html:
                logger.warning("TAIKAI returned empty content", url=url)
                continue
            
            # Strategy 2: Extract from __NEXT_DATA__
            next_data_events = extract_next_data(html)
            if next_data_events:
                logger.info("TAIKAI __NEXT_DATA__ extraction success", count=len(next_data_events))
                all_events.extend(next_data_events)
                continue
            
            # Strategy 3: Extract from Apollo State (for Apollo Client apps)
            apollo_events = extract_apollo_state(html)
            if apollo_events:
                logger.info("TAIKAI Apollo State extraction success", count=len(apollo_events))
                all_events.extend(apollo_events)
                continue
            
            # Strategy 4: HTML parsing as fallback
            html_events = parse_taikai_html(html)
            if html_events:
                logger.info("TAIKAI HTML parsing success", count=len(html_events))
                all_events.extend(html_events)
                
        except Exception as e:
            logger.warning("TAIKAI fetch failed", url=url, error=str(e))
    
    # Deduplicate by slug
    unique_events = {e.get('slug', e.get('name', '')): e for e in all_events if e.get('slug') or e.get('name')}
    
    return list(unique_events.values())


async def fetch_taikai_graphql() -> List[Dict[str, Any]]:
    """
    Try to fetch from TAIKAI's GraphQL API.
    """
    import httpx
    
    query = """
    query GetHackathons($status: [ChallengeStatus!]) {
        challenges(status: $status, first: 50) {
            edges {
                node {
                    id
                    name
                    slug
                    shortDescription
                    prizePool
                    startDate
                    endDate
                    registrationDeadline
                    type
                    organization {
                        name
                        slug
                    }
                }
            }
        }
    }
    """
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                TAIKAI_API_URL,
                json={
                    "query": query,
                    "variables": {"status": ["OPEN", "UPCOMING"]}
                },
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                edges = data.get('data', {}).get('challenges', {}).get('edges', [])
                return [edge.get('node', {}) for edge in edges if edge.get('node')]
                
    except Exception as e:
        logger.debug("TAIKAI GraphQL request failed", error=str(e))
    
    return []


def extract_next_data(html: str) -> List[Dict[str, Any]]:
    """
    Extract hackathons from Next.js __NEXT_DATA__ script.
    """
    try:
        match = re.search(
            r'<script id="__NEXT_DATA__"[^>]*type="application/json"[^>]*>(.*?)</script>',
            html,
            re.DOTALL
        )
        
        if not match:
            return []
        
        data = json.loads(match.group(1))
        
        # Try various paths to find challenges/hackathons
        page_props = data.get('props', {}).get('pageProps', {})
        
        # Direct challenges list
        challenges = page_props.get('challenges', [])
        if challenges:
            return challenges
        
        # In initialState
        initial_state = page_props.get('initialState', {})
        challenges = initial_state.get('challenges', {}).get('list', [])
        if challenges:
            return challenges
        
        # In dehydratedState (React Query)
        dehydrated = page_props.get('dehydratedState', {})
        queries = dehydrated.get('queries', [])
        for q in queries:
            query_data = q.get('state', {}).get('data', {})
            if isinstance(query_data, list):
                return query_data
            elif isinstance(query_data, dict):
                items = query_data.get('items', []) or query_data.get('challenges', []) or query_data.get('edges', [])
                if items:
                    # Handle edge format
                    if items and isinstance(items[0], dict) and 'node' in items[0]:
                        return [item.get('node', {}) for item in items]
                    return items
        
        # Recursive search for challenge-like objects
        def find_challenges(obj, found=None):
            if found is None:
                found = []
            if isinstance(obj, dict):
                if 'slug' in obj and ('prizePool' in obj or 'name' in obj or 'endDate' in obj):
                    if obj.get('__typename', '').lower() in ['challenge', 'hackathon', ''] or 'organization' in obj:
                        found.append(obj)
                for v in obj.values():
                    find_challenges(v, found)
            elif isinstance(obj, list):
                for item in obj:
                    find_challenges(item, found)
            return found
        
        challenges = find_challenges(data)
        # Deduplicate
        unique = {c.get('slug', ''): c for c in challenges if c.get('slug')}
        return list(unique.values())
        
    except Exception as e:
        logger.debug("TAIKAI __NEXT_DATA__ extraction failed", error=str(e))
        return []


def extract_apollo_state(html: str) -> List[Dict[str, Any]]:
    """
    Extract from Apollo Client state embedded in the page.
    """
    try:
        match = re.search(
            r'<script id="__NEXT_DATA__"[^>]*type="application/json"[^>]*>(.*?)</script>',
            html,
            re.DOTALL
        )
        
        if not match:
            return []
        
        data = json.loads(match.group(1))
        page_props = data.get('props', {}).get('pageProps', {})
        apollo_state = page_props.get('apolloState', {})
        
        if not apollo_state:
            return []
        
        challenges = []
        for key, value in apollo_state.items():
            if not isinstance(value, dict):
                continue
            
            # Look for Challenge objects
            if key.startswith('Challenge:') or value.get('__typename') == 'Challenge':
                if 'name' in value and 'slug' in value:
                    # Ensure it has actual data, not just references
                    if 'prizePool' in value or 'shortDescription' in value or 'endDate' in value:
                        challenges.append(value)
        
        return challenges
        
    except Exception as e:
        logger.debug("TAIKAI Apollo State extraction failed", error=str(e))
        return []


def parse_taikai_html(html: str) -> List[Dict[str, Any]]:
    """
    Parse TAIKAI hackathon cards from HTML as final fallback.
    """
    from bs4 import BeautifulSoup
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        events = []
        
        # TAIKAI uses card-based layout
        cards = soup.select('[class*="challenge"], [class*="hackathon"], [class*="card"]')
        
        for card in cards:
            try:
                # Name
                name_el = card.select_one('h2, h3, h4, [class*="title"], [class*="name"]')
                name = name_el.get_text(strip=True) if name_el else None
                
                if not name or len(name) < 3:
                    continue
                
                # URL/slug
                link_el = card.select_one('a[href*="/hackathons/"]')
                href = link_el.get('href', '') if link_el else ''
                slug_match = re.search(r'/hackathons/([^/]+)', href)
                slug = slug_match.group(1) if slug_match else ''
                
                # Prize
                prize_el = card.select_one('[class*="prize"], [class*="reward"]')
                prize_text = prize_el.get_text(strip=True) if prize_el else ''
                
                # Organization
                org_el = card.select_one('[class*="organization"], [class*="sponsor"]')
                org_name = org_el.get_text(strip=True) if org_el else 'TAIKAI'
                
                events.append({
                    'name': name,
                    'slug': slug,
                    'prizePool': prize_text,
                    'organization': {'name': org_name, 'slug': 'taikai'}
                })
                
            except Exception:
                continue
        
        return events
        
    except Exception as e:
        logger.debug("TAIKAI HTML parsing failed", error=str(e))
        return []


def transform_taikai_event(event: Dict[str, Any]) -> Optional[Scholarship]:
    """
    Transform TAIKAI event data to Scholarship model.
    """
    try:
        title = event.get('name', '') or event.get('title', '')
        slug = event.get('slug', '')
        
        if not title:
            return None
        
        # Construct URL
        org = event.get('organization', {})
        org_slug = org.get('slug', 'taikai') if isinstance(org, dict) else 'taikai'
        url = f"https://taikai.network/{org_slug}/hackathons/{slug}" if slug else "https://taikai.network/hackathons"
        
        # Parse Prize
        amount = 0
        prize_pool = event.get('prizePool', '0') or event.get('prize', '0')
        try:
            # Clean string like "$10,000" or "10000 USD" or "€5,000"
            clean_prize = str(prize_pool).replace('$', '').replace('€', '').replace(',', '').replace(' ', '')
            # Extract numeric part
            num_match = re.search(r'(\d+(?:\.\d+)?)', clean_prize)
            if num_match:
                amount = int(float(num_match.group(1)))
        except ValueError:
            pass
        
        amount_display = str(prize_pool) if prize_pool and prize_pool != '0' else 'Varies'
        
        # Parse Dates
        deadline = None
        deadline_timestamp = None
        end_date = event.get('endDate') or event.get('registrationDeadline') or event.get('end_date')
        
        if end_date:
            try:
                if isinstance(end_date, str):
                    deadline_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                else:
                    deadline_dt = datetime.fromtimestamp(end_date / 1000 if end_date > 1e10 else end_date)
                deadline = deadline_dt.strftime('%Y-%m-%d')
                deadline_timestamp = int(deadline_dt.timestamp())
            except Exception:
                pass
        
        # Tags and Metadata
        tags = ['Hackathon', 'TAIKAI']
        event_tags = event.get('tags', [])
        if isinstance(event_tags, list):
            tags.extend([str(t) for t in event_tags[:3]])
        
        event_type = event.get('type', '')
        location = "Online" if 'online' in str(event_type).lower() else event.get('location', 'Global')
        
        org_name = org.get('name', 'TAIKAI') if isinstance(org, dict) else 'TAIKAI'
        
        opportunity_data = {
            'id': '',
            'name': title,
            'title': title,
            'organization': org_name,
            'amount': amount,
            'amount_display': amount_display,
            'deadline': deadline,
            'deadline_timestamp': deadline_timestamp,
            'source_url': url,
            'description': event.get('shortDescription', '') or event.get('description', '')[:500] or f"Join the {title} hackathon on TAIKAI. Build innovative solutions and compete for prizes.",
            'tags': tags,
            'geo_tags': ['Global', 'Online'] if 'Online' in str(location) else [location],
            'type_tags': ['Hackathon'],
            'eligibility': {
                'gpa_min': None,
                'majors': [],
                'states': [],
                'citizenship': 'any',
                'grade_levels': []
            },
            'eligibility_text': 'Open to developers globally',
            'source_type': 'taikai',
            'match_score': 50,
            'match_tier': 'Good',
            'verified': True,
            'last_verified': datetime.now().isoformat(),
            'priority_level': 'HIGH' if amount >= 5000 else 'MEDIUM'
        }
        
        opportunity_data['id'] = generate_opportunity_id(opportunity_data)
        return Scholarship(**opportunity_data)

    except Exception as e:
        logger.warning("TAIKAI transform failed", error=str(e), event=event.get('name', 'Unknown'))
        return None


async def scrape_taikai_events() -> List[Scholarship]:
    """Main scraping function for TAIKAI"""
    logger.info("Starting TAIKAI scrape (Enhanced Playwright mode)...")
    events = await fetch_taikai_events()
    
    scholarships = []
    for event in events:
        s = transform_taikai_event(event)
        if s:
            scholarships.append(s)
            
    logger.info("TAIKAI scrape complete", count=len(scholarships))
    return scholarships


async def populate_database_with_taikai() -> int:
    """Scrape and save to DB"""
    scholarships = await scrape_taikai_events()
    count = 0
    for s in scholarships:
        try:
            await db.save_scholarship(s)
            count += 1
        except Exception as e:
            logger.warning("Failed to save TAIKAI event", id=s.id, error=str(e))
    
    logger.info("TAIKAI database population complete", saved=count)
    return count


if __name__ == "__main__":
    async def main():
        scholarships = await scrape_taikai_events()
        print(f"\nFound {len(scholarships)} TAIKAI events:")
        for s in scholarships:
            print(f"  - {s.name}: {s.amount_display}")
            print(f"    URL: {s.source_url}")
    
    asyncio.run(main())
