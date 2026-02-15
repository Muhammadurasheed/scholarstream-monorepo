"""
MLH (Major League Hacking) Scraper - PLAYWRIGHT EDITION
Fetches hackathon events from MLH using Playwright to bypass anti-bot measures.

Bismillah - Enhanced for reliability with multiple fallback strategies.
"""
import asyncio
import json
import re
import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.flink_processor import generate_opportunity_id
from app.database import db
from app.models import Scholarship
from app.services.crawler_service import crawler_service

logger = structlog.get_logger()

# MLH event pages for different seasons
MLH_URLS = [
    "https://mlh.io/seasons/2026/events",
    "https://mlh.io/seasons/2025/events",
]


async def fetch_mlh_events() -> List[Dict[str, Any]]:
    """
    Fetch MLH hackathon events using Playwright (via crawler_service).
    Multiple fallback strategies for maximum reliability.
    """
    all_events = []
    
    for url in MLH_URLS:
        try:
            logger.info("Fetching MLH events via Playwright", url=url)
            html = await crawler_service.fetch_content(url)
            
            if not html:
                logger.warning("MLH returned empty content", url=url)
                continue
            
            # Strategy 1: Parse HTML structure directly
            # MLH event cards have a specific structure with data attributes
            events_from_html = parse_mlh_html(html)
            if events_from_html:
                logger.info("MLH HTML parsing success", url=url, count=len(events_from_html))
                all_events.extend(events_from_html)
                continue
            
            # Strategy 2: Look for embedded JSON data
            # MLH sometimes has window.__DATA__ or similar
            json_patterns = [
                r'window\.__EVENTS__\s*=\s*(\[.*?\]);',
                r'window\.mlhEvents\s*=\s*(\[.*?\]);',
                r'"events"\s*:\s*(\[.*?\])',
                r'<script[^>]*type="application/json"[^>]*>(.*?)</script>',
            ]
            
            for pattern in json_patterns:
                match = re.search(pattern, html, re.DOTALL)
                if match:
                    try:
                        data = json.loads(match.group(1))
                        if isinstance(data, list) and len(data) > 0:
                            logger.info("MLH JSON extraction success", pattern=pattern[:30], count=len(data))
                            all_events.extend(data)
                            break
                    except json.JSONDecodeError:
                        continue
            
        except Exception as e:
            logger.warning("MLH fetch failed", url=url, error=str(e))
    
    # Deduplicate by name
    unique_events = {e.get('name', e.get('title', '')): e for e in all_events if e.get('name') or e.get('title')}
    
    return list(unique_events.values())



def parse_mlh_html(html: str) -> List[Dict[str, Any]]:
    """
    Parse MLH event cards from HTML.
    MLH uses a specific card structure with event details.
    """
    from bs4 import BeautifulSoup
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        events = []
        
        # MLH event cards typically have class 'event' or 'event-wrapper'
        event_cards = soup.select('.event, .event-wrapper, [class*="event-card"], [data-event]')
        
        if not event_cards:
            # Try finding by structure: divs containing h3/h4 with links
            event_cards = soup.select('div[class*="card"]')
        
        for card in event_cards:
            try:
                # Extract name
                name_el = card.select_one('h3, h4, .event-name, [class*="name"], [class*="title"]')
                name = name_el.get_text(strip=True) if name_el else None
                
                if not name or len(name) < 3:
                    continue
                
                # Extract URL
                link_el = card.select_one('a[href]')
                url = link_el.get('href', '') if link_el else ''
                if url and not url.startswith('http'):
                    url = f"https://mlh.io{url}" if url.startswith('/') else f"https://{url}"
                
                # Extract location
                location_el = card.select_one('.event-location, [class*="location"], [class*="city"]')
                location = location_el.get_text(strip=True) if location_el else 'TBD'
                
                # Extract dates
                date_el = card.select_one('.event-date, [class*="date"], time')
                date_text = date_el.get_text(strip=True) if date_el else ''
                
                # Check if hybrid/online
                is_online = 'digital' in card.get_text().lower() or 'online' in card.get_text().lower() or 'virtual' in card.get_text().lower()
                
                events.append({
                    'name': name,
                    'url': url,
                    'location': location,
                    'date_text': date_text,
                    'is_online': is_online
                })
                
            except Exception as e:
                logger.debug("Failed to parse MLH event card", error=str(e))
                continue
        
        return events
        
    except Exception as e:
        logger.debug("MLH HTML parsing failed", error=str(e))
        return []


def _parse_mlh_date_text(date_text: str) -> Optional[datetime]:
    """Parse MLH card date text like 'Jan 10 – 12, 2026' or 'Jan 10, 2026'.

    Returns the END date when a range is provided (that's when the hackathon ends).
    """
    if not date_text:
        return None

    # Normalize dashes
    t = date_text.replace('\u2013', '-').replace('–', '-').strip()

    # Pattern 1: "Jan 10 - 12, 2026" or "January 10 - 12, 2026" (date range, same month)
    m = re.search(r'([A-Za-z]+)\s+(\d{1,2})\s*-\s*(\d{1,2}),?\s*(\d{4})', t)
    if m:
        month, _start_day, end_day, year = m.group(1), m.group(2), m.group(3), m.group(4)
        for fmt in ['%b %d %Y', '%B %d %Y']:
            try:
                return datetime.strptime(f"{month} {end_day} {year}", fmt)
            except ValueError:
                continue

    # Pattern 2: "Jan 10, 2026" / "January 10, 2026" (single date)
    for fmt in ['%b %d, %Y', '%B %d, %Y', '%b %d %Y', '%B %d %Y']:
        try:
            return datetime.strptime(t, fmt)
        except ValueError:
            continue

    # Pattern 3: "10 Jan 2026" / "10 January 2026"
    for fmt in ['%d %b %Y', '%d %B %Y']:
        try:
            return datetime.strptime(t, fmt)
        except ValueError:
            continue

    return None


def transform_mlh_event(event: Dict[str, Any]) -> Optional[Scholarship]:
    """
    Transform MLH event data to Scholarship model.
    """
    try:
        name = event.get('name', '') or event.get('title', '')
        url = event.get('url', '') or event.get('website', '') or event.get('link', '')

        if not name:
            return None

        if not url or not url.startswith('http'):
            # Create MLH-style URL
            slug = name.lower().replace(' ', '-').replace('.', '')
            url = f"https://mlh.io/events/{slug}"

        # Parse dates
        deadline = None
        deadline_timestamp = None

        # Try different date fields first
        end_date = event.get('end_date') or event.get('endDate') or event.get('end')
        start_date = event.get('start_date') or event.get('startDate') or event.get('start')

        date_to_use = end_date or start_date

        if date_to_use:
            try:
                if isinstance(date_to_use, str):
                    # Handle various date formats
                    for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%B %d, %Y', '%m/%d/%Y']:
                        try:
                            deadline_dt = datetime.strptime(date_to_use.split('T')[0].split('+')[0], fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        deadline_dt = datetime.fromisoformat(date_to_use.replace('Z', '+00:00'))
                else:
                    deadline_dt = datetime.fromtimestamp(date_to_use / 1000 if date_to_use > 1e10 else date_to_use)

                deadline = deadline_dt.strftime('%Y-%m-%d')
                deadline_timestamp = int(deadline_dt.timestamp())

            except Exception:
                pass

        # V3 FIX: If no structured date fields, parse the card's date_text (e.g., "Jan 10 – 12, 2026")
        if not deadline:
            dt = _parse_mlh_date_text(str(event.get('date_text') or ''))
            if dt:
                deadline = dt.strftime('%Y-%m-%d')
                deadline_timestamp = int(dt.timestamp())
                logger.debug(f"MLH date_text parsed: {event.get('date_text')} -> {deadline}")

        location = event.get('location', '') or event.get('city', 'TBD')
        is_online = event.get('is_online', False) or 'online' in str(location).lower() or 'virtual' in str(location).lower()
        
        # V2 FIX: Better prize display for MLH events
        # MLH hackathons typically have sponsor prizes ($500-$5000+ per category)
        # Also include swag (MLH is known for great swag packages)
        prize_info = event.get('prizes', [])
        prize_amount = 0
        prize_display = 'View Prizes →'  # Default with call-to-action
        
        if prize_info:
            # If we have prize data, sum it up
            total = sum(p.get('value', 0) for p in prize_info if isinstance(p, dict))
            if total > 0:
                prize_amount = total
                prize_display = f'${total:,} in prizes'
        else:
            # MLH events always have sponsor prizes even if not explicitly listed
            # Typical MLH hackathon has $1000-$10000 in prizes + swag
            prize_display = 'Prizes + Swag (View Details)'
        
        opportunity_data = {
            'id': '',
            'name': name,
            'title': name,
            'organization': 'Major League Hacking (MLH)',
            'amount': prize_amount,
            'amount_display': prize_display,
            'deadline': deadline,
            'deadline_timestamp': deadline_timestamp,
            'source_url': url,
            'description': f"MLH hackathon at {location}. Join students from around the world to build, learn, and share. MLH is the official student hackathon league. Open to students globally - virtual participation often available.",
            'tags': ['Hackathon', 'MLH', 'Student', 'Global', 'Online' if is_online else 'In-Person'],
            'geo_tags': ['Global', 'International', 'Online'] if is_online else ['Global', location],
            'type_tags': ['Hackathon', 'Competition'],
            'eligibility': {
                'gpa_min': None,
                'majors': [],
                'states': [],
                'citizenship': 'any',  # V2: Explicitly global
                'grade_levels': ['High School', 'Undergraduate', 'Graduate']
            },
            'eligibility_text': 'Open to all students worldwide (high school and university)',
            'source_type': 'mlh',
            'match_score': 0.0,  # Will be calculated dynamically
            'match_tier': 'Good',
            'verified': True,
            'last_verified': datetime.now().isoformat(),
            'priority_level': 'HIGH'
        }
        
        opportunity_data['id'] = generate_opportunity_id(opportunity_data)
        return Scholarship(**opportunity_data)
        
    except Exception as e:
        logger.warning("MLH transform failed", error=str(e), event=event.get('name', 'Unknown'))
        return None


async def scrape_mlh_events() -> List[Scholarship]:
    """
    Main function to scrape MLH hackathons.
    """
    logger.info("Starting MLH scrape (Playwright mode)")
    
    events = await fetch_mlh_events()
    scholarships = []
    
    for event in events:
        scholarship = transform_mlh_event(event)
        if scholarship:
            scholarships.append(scholarship)
    
    logger.info("MLH scrape complete", total=len(scholarships))
    return scholarships


async def populate_database_with_mlh() -> int:
    """
    Scrape MLH and save to Firestore.
    """
    logger.info("Populating database with MLH events...")
    
    scholarships = await scrape_mlh_events()
    
    saved_count = 0
    for scholarship in scholarships:
        try:
            await db.save_scholarship(scholarship)
            saved_count += 1
        except Exception as e:
            logger.warning("Failed to save MLH event", id=scholarship.id, error=str(e))
    
    logger.info("MLH population complete", saved=saved_count)
    return saved_count


if __name__ == "__main__":
    async def main():
        scholarships = await scrape_mlh_events()
        print(f"\nFound {len(scholarships)} MLH events:")
        for s in scholarships:
            print(f"  - {s.name}: {s.deadline}")
            print(f"    URL: {s.source_url}")
    
    asyncio.run(main())
