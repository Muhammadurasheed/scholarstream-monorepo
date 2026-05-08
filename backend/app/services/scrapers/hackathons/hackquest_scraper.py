"""
HackQuest Scraper
Fetches hackathons from HackQuest using GraphQL API.
"""
import httpx
import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.flink_processor import generate_opportunity_id
from app.database import db
from app.models import Scholarship

logger = structlog.get_logger()

GRAPHQL_URL = "https://api.hackquest.io/graphql"

# Standard query reversed from browser network logs
# We ask for a broad list of active/upcoming hackathons
QUERY = """
query ListHackathons($where: HackathonsWhereInput, $orderBy: [HackathonsOrderByInput!], $skip: Int, $take: Int) {
  hackathons(where: $where, orderBy: $orderBy, skip: $skip, take: $take) {
    id
    name
    alias
    description
    status
    startTime
    endTime
    rewards {
        amount
        currency
    }
    ecosystem {
        name
    }
    tracks {
        name
    }
  }
}
"""

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Origin': 'https://www.hackquest.io',
    'Referer': 'https://www.hackquest.io/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'Connection': 'keep-alive'
}


from app.services.crawler_service import crawler_service
import asyncio
import json



# Removed duplicate/stub function definition


async def fetch_hackquest_events() -> List[Dict[str, Any]]:
    """
    Fetch HackQuest hackathons by scraping the frontend directly.
    The GraphQL API is CORS-strict, so we parse the hydration state from the page.
    """
    try:
        url = "https://www.hackquest.io/hackathons"
        logger.info("HackQuest Drone approaching frontend...")
        
        # Get full page HTML (FIXED: removed duplicate fetch call)
        html = await crawler_service.fetch_content(url)
        
        if not html:
            logger.warning("HackQuest fetch returned empty content")
            return []
        
        # PRIORITY 1: Try to extract from __NEXT_DATA__ (more stable than DOM)
        import re
        next_data_match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
        if next_data_match:
            try:
                data = json.loads(next_data_match.group(1))
                # Search for hackathon objects in the hydration state
                def find_hackathons(obj, found=None):
                    if found is None:
                        found = []
                    if isinstance(obj, dict):
                        # HackQuest hackathon objects usually have 'alias' and 'name' fields
                        if 'alias' in obj and 'name' in obj and isinstance(obj.get('name'), str):
                            found.append(obj)
                        for v in obj.values():
                            find_hackathons(v, found)
                    elif isinstance(obj, list):
                        for item in obj:
                            find_hackathons(item, found)
                    return found
                
                hackathons = find_hackathons(data)
                # Deduplicate by alias
                unique = {h.get('alias', h.get('id', '')): h for h in hackathons if h.get('alias') or h.get('id')}
                if unique:
                    logger.info("HackQuest __NEXT_DATA__ parse success", count=len(unique))
                    return list(unique.values())
            except Exception as e:
                logger.debug("HackQuest __NEXT_DATA__ parse failed, falling back to DOM", error=str(e))
        
        # FALLBACK: DOM scraping with BeautifulSoup
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Helper to find hackathons via DOM
        # Selector: a[href^='/hackathons/']
        cards = soup.select("a[href^='/hackathons/']")
        serialized_events = []
        
        for card in cards:
            try:
                # Title is usually in an h2
                title_tag = card.find('h2')
                if not title_tag:
                    continue
                title = title_tag.get_text(strip=True)
                
                href = card.get('href', '')
                alias = href.split('/')[-1] if href else ''
                
                # Status/Deadline often in generic divs. 
                # We grab all text to verify it's a valid card
                text_content = card.get_text(" ", strip=True)
                
                # Basic reconstruction of an event object
                event = {
                    "id": alias,  # use alias as ID
                    "name": title,
                    "alias": alias,
                    "description": text_content[:200],  # approximate
                    "endTime": None  # scraped DOM usually doesn't have easy ISO dates
                }
                
                # Attempt to find prize
                # Look for text like "USD" or "$"
                if "$" in text_content or "USD" in text_content:
                    # Extract basic number
                    prize_match = re.search(r'\$?([\d,]+)\s*USD', text_content)
                    if prize_match:
                        event["rewards"] = [{"amount": prize_match.group(1).replace(',', '')}]
                
                if title:
                    serialized_events.append(event)
                    
            except Exception:
                continue
        
        # Deduplicate by alias
        unique = {e['alias']: e for e in serialized_events}.values()
        
        if unique:
            logger.info("HackQuest DOM scrape success", count=len(unique))
            return list(unique)

    except Exception as e:
        logger.warning("HackQuest frontend scrape failed", error=str(e))

    return []

def transform_hackquest_event(event: Dict[str, Any]) -> Optional[Scholarship]:
    """
    Transform HackQuest event data to Scholarship model.
    """
    try:
        title = event.get('name', '')
        alias = event.get('alias', '')
        
        if not title:
            return None
            
        url = f"https://www.hackquest.io/hackathons/{alias}" if alias else "https://www.hackquest.io/hackathons"
        
        # Parse Prize
        amount = 0
        rewards = event.get('rewards', [])
        if rewards:
             # Sum up or take max. Usually it's a prize pool.
             # Simplified: just take first amount found
             try:
                 amount = float(rewards[0].get('amount', 0))
             except:
                 pass
        
        amount_display = f"${amount:,.0f}" if amount > 0 else "Varies"
        
        # Parse Dates
        deadline = None
        deadline_timestamp = None
        end_time = event.get('endTime')
        
        if end_time:
            try:
                deadline_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                deadline = deadline_dt.strftime('%Y-%m-%d')
                deadline_timestamp = int(deadline_dt.timestamp())
            except:
                pass
        
        # Tags
        tags = ['Hackathon', 'HackQuest']
        ecosystem = event.get('ecosystem', {})
        if ecosystem and ecosystem.get('name'):
            tags.append(ecosystem.get('name'))
            
        for track in event.get('tracks', [])[:2]:
            if track.get('name'):
                tags.append(track.get('name'))

        opportunity_data = {
            'id': '',
            'name': title,
            'title': title,
            'organization': 'HackQuest',
            'amount': amount,
            'amount_display': amount_display,
            'deadline': deadline,
            'deadline_timestamp': deadline_timestamp,
            'source_url': url,
            'description': event.get('description', '')[:500] if event.get('description') else f"Join {title} on HackQuest.",
            'tags': tags,
            'geo_tags': ['Global', 'Online'],
            'type_tags': ['Hackathon'],
            'eligibility': {
                'gpa_min': None,
                'majors': [],
                'states': [],
                'citizenship': 'any',
                'grade_levels': []
            },
            'eligibility_text': 'Open to Web3 developers',
            'source_type': 'hackquest',
            'match_score': 50,
            'match_tier': 'Good',
            'verified': True,
            'last_verified': datetime.now().isoformat(),
            'priority_level': 'HIGH' if amount >= 5000 else 'MEDIUM'
        }
        
        opportunity_data['id'] = generate_opportunity_id(opportunity_data)
        return Scholarship(**opportunity_data)

    except Exception as e:
        logger.warning("HackQuest transform failed", error=str(e), event=event.get('name', 'Unknown'))
        return None

async def scrape_hackquest_events() -> List[Scholarship]:
    """Main scraping function for HackQuest"""
    logger.info("Starting HackQuest scrape...")
    events = await fetch_hackquest_events()
    
    scholarships = []
    for event in events:
        s = transform_hackquest_event(event)
        if s:
            scholarships.append(s)
            
    logger.info("HackQuest scrape complete", count=len(scholarships))
    return scholarships

async def populate_database_with_hackquest() -> int:
    """Scrape and save to DB"""
    scholarships = await scrape_hackquest_events()
    count = 0
    for s in scholarships:
        try:
            await db.save_scholarship(s)
            count += 1
        except Exception:
            pass
    return count
