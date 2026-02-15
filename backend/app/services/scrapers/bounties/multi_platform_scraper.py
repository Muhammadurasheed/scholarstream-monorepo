"""
Multi-Platform Opportunity Scrapers
Creates scrapers for DoraHacks, HackQuest, Immunefi, Superteam, and other bounty platforms.
"""
import httpx
import asyncio
import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urljoin

from app.services.flink_processor import generate_opportunity_id
from app.database import db
from app.models import Scholarship

logger = structlog.get_logger()

# Common headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'Connection': 'keep-alive'
}



from app.services.crawler_service import crawler_service
import json

# ========================================
# DORAHACKS SCRAPER
# ========================================
DORAHACKS_GRAPHQL_URL = "https://dorahacks.io/graphql"

async def fetch_dorahacks_hackathons() -> List[Dict[str, Any]]:
    """
    Fetch hackathons from DoraHacks using Sentinel Drone to bypass WAF.
    Enhanced with schema-tolerant JSON parsing for various API response formats.
    """
    import re
    
    def extract_json_from_content(content: str) -> Any:
        """Extract JSON from browser-rendered content (handles <pre> wrapping)"""
        if not content:
            return None
        
        # Try to extract JSON from Pre tag if wrapped by browser
        pre_match = re.search(r'<pre[^>]*>(.*?)</pre>', content, re.DOTALL)
        json_text = pre_match.group(1) if pre_match else content
        
        # Clean HTML entities
        json_text = json_text.replace('&quot;', '"').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        
        # Try array first (common for list endpoints)
        start_list = json_text.find('[')
        start_obj = json_text.find('{')
        
        if start_list != -1 and (start_obj == -1 or start_list < start_obj):
            end = json_text.rfind(']')
            if end != -1:
                try:
                    return json.loads(json_text[start_list:end+1])
                except:
                    pass
        
        # Try object
        if start_obj != -1:
            end = json_text.rfind('}')
            if end != -1:
                try:
                    return json.loads(json_text[start_obj:end+1])
                except:
                    pass
        
        return None
    
    def extract_hackathons_from_data(data: Any) -> List[Dict[str, Any]]:
        """Schema-tolerant extraction: handles {results: []}, {items: []}, {data: []}, [...], etc."""
        if isinstance(data, list):
            return data
        
        if isinstance(data, dict):
            # Try common API response patterns
            for key in ['results', 'items', 'data', 'hackathons', 'list', 'records']:
                val = data.get(key)
                if isinstance(val, list):
                    return val
                if isinstance(val, dict):
                    # Nested: {data: {list: []}} or {data: {items: []}}
                    for subkey in ['list', 'items', 'results', 'hackathons']:
                        subval = val.get(subkey)
                        if isinstance(subval, list):
                            return subval
        
        return []
    
    try:
        # Try multiple API endpoints (DoraHacks has changed their API structure before)
        api_urls = [
            "https://dorahacks.io/api/hackathon?page=1&page_size=50&status=active",
            "https://dorahacks.io/api/hackathon/list?page=1&limit=50",
            "https://dorahacks.io/api/v1/hackathon?status=active&limit=50",
        ]
        
        all_hackathons = []
        
        for api_url in api_urls:
            logger.info("Fetching DoraHacks via API", url=api_url)
            content = await crawler_service.fetch_content(api_url)
            
            if content:
                data = extract_json_from_content(content)
                if data:
                    hackathons = extract_hackathons_from_data(data)
                    if hackathons:
                        logger.info("DoraHacks API success", url=api_url, count=len(hackathons))
                        all_hackathons.extend(hackathons)
                        break  # Stop if we got results
        
        if all_hackathons:
            return all_hackathons
        
        # Fallback: Scrape Frontend if all APIs failed
        logger.info("DoraHacks API endpoints returned no data, attempting frontend scrape...")
        frontend_url = "https://dorahacks.io/hackathon"
        html = await crawler_service.fetch_content(frontend_url)
        
        if html:
            # Look for __NEXT_DATA__
            match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    
                    # Recursive search for hackathon-like objects
                    def find_hackathons(obj, found=None):
                        if found is None:
                            found = []
                        if isinstance(obj, dict):
                            # DoraHacks hackathons have 'slug' and often 'totalPrize' or 'name'
                            if 'slug' in obj and ('totalPrize' in obj or 'name' in obj or 'title' in obj):
                                found.append(obj)
                            for v in obj.values():
                                find_hackathons(v, found)
                        elif isinstance(obj, list):
                            for item in obj:
                                find_hackathons(item, found)
                        return found
                    
                    hackathons = find_hackathons(data)
                    # Deduplicate by slug
                    unique = {h.get('slug', ''): h for h in hackathons if h.get('slug')}
                    if unique:
                        logger.info("DoraHacks frontend scrape success", count=len(unique))
                        return list(unique.values())
                except Exception as e:
                    logger.debug("DoraHacks __NEXT_DATA__ parse failed", error=str(e))

    except Exception as e:
        logger.warning("DoraHacks fetch failed", error=str(e))
    
    return []


async def fetch_dorahacks_bounties() -> List[Dict[str, Any]]:
    """Fetch bounties from DoraHacks"""
    try:
        url = "https://dorahacks.io/api/bounty/list?status=open&page=1&limit=50"
        content = await crawler_service.fetch_content(url)
        
        if content:
             import re
             pre_match = re.search(r'<pre[^>]*>(.*?)</pre>', content, re.DOTALL)
             json_text = pre_match.group(1) if pre_match else content
             json_text = json_text.replace('&quot;', '"').replace('&lt;', '<').replace('&gt;', '>')
             
             start = json_text.find('{')
             end = json_text.rfind('}')
             if start != -1 and end != -1:
                 try:
                     data = json.loads(json_text[start:end+1])
                     bounties = data.get('data', {}).get('list', []) if isinstance(data, dict) else []
                     logger.info("DoraHacks bounties fetched", count=len(bounties))
                     return bounties
                 except:
                     pass
                     
    except Exception as e:
        logger.warning("DoraHacks bounties fetch failed", error=str(e))
    
    return []


def transform_dorahacks_hackathon(item: Dict[str, Any]) -> Optional[Scholarship]:
    """Transform DoraHacks hackathon to Scholarship model"""
    # DEBUG
    # print(f"DEBUG: Raw Dora Item keys: {item.keys()}")
    try:
        title = item.get('name') or item.get('title', '')
        slug = item.get('slug') or item.get('uname') or item.get('alias', '')
        
        if not title or not slug:
            # DEBUG: Print exact values to diagnose why validation fails
            # logger.warning("DoraHacks validation failed", title=title, slug=slug, keys=list(item.keys()))
            # print(f"DEBUG: DoraHacks MISSING. Title='{title}' Slug='{slug}' Keys={list(item.keys())}")
            # Try to recover title if name is None but slug isn't
            if slug and not title:
                 title = slug.replace('-', ' ').title()
            
            if not title or not slug:
                 return None
        
        url = f"https://dorahacks.io/hackathon/{slug}"
        
        # Parse prize (DoraHacks fields vary across endpoints/versions)
        # ENHANCED: More aggressive prize extraction from all possible fields
        def _parse_amount(value: Any) -> int:
            try:
                if value is None:
                    return 0
                if isinstance(value, (int, float)):
                    return int(value) if value > 0 else 0
                if isinstance(value, dict):
                    # Try many possible keys in dict
                    for key in ['amount', 'value', 'max', 'total', 'usd', 'usdc', 'prize']:
                        if key in value:
                            result = _parse_amount(value[key])
                            if result > 0:
                                return result
                    # Sum all numeric values in dict as fallback
                    total = 0
                    for v in value.values():
                        if isinstance(v, (int, float)) and v > 0:
                            total += int(v)
                    return total
                if isinstance(value, list) and value:
                    # Sum prizes from array of tiers/prizes
                    return sum((_parse_amount(v) for v in value), 0)
                s = str(value).replace('$', '').replace(',', '').strip()
                import re
                # Match numbers with optional K/M suffix
                m = re.search(r"([\d.]+)\s*([KkMm])?", s)
                if m:
                    num = float(m.group(1))
                    suffix = (m.group(2) or '').upper()
                    if suffix == 'K':
                        num *= 1000
                    elif suffix == 'M':
                        num *= 1000000
                    return int(num)
                return 0
            except Exception:
                return 0

        # Try ALL possible prize fields aggressively
        amount = 0
        for field in ['totalPrize', 'total_prize', 'prizePool', 'prize_pool', 
                      'reward', 'rewards', 'prize', 'bounty', 'totalReward',
                      'total_reward', 'prizeAmount', 'prize_amount', 'bonus',
                      'maxPrize', 'max_prize', 'totalBounty', 'prizeMoney']:
            raw = item.get(field)
            if raw:
                parsed = _parse_amount(raw)
                if parsed > amount:
                    amount = parsed
        
        # Also check nested 'prize' or 'rewards' objects
        if amount == 0:
            prize_obj = item.get('prize') or item.get('rewards') or item.get('prizeInfo') or {}
            if isinstance(prize_obj, dict):
                for key in ['total', 'amount', 'usd', 'value', 'max']:
                    if key in prize_obj:
                        parsed = _parse_amount(prize_obj[key])
                        if parsed > amount:
                            amount = parsed

        prize_unit = item.get('prizeUnit', 'USD')
        amount_display = f"${amount:,}" if (prize_unit or '').upper() == 'USD' and amount > 0 else (item.get('totalPrizeText') or item.get('prizePool') or (f"{amount:,} {prize_unit}" if amount > 0 else "Varies"))
        
        # Parse deadline
        deadline = None
        deadline_timestamp = None
        end_time = item.get('endTime')
        if end_time:
            try:
                if isinstance(end_time, str):
                    deadline_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                else:
                    deadline_dt = datetime.fromtimestamp(end_time / 1000)
                deadline = deadline_dt.strftime('%Y-%m-%d')
                deadline_timestamp = int(deadline_dt.timestamp())
            except:
                pass
        
        opportunity_data = {
            'id': '',
            'name': title,
            'title': title,
            'organization': 'DoraHacks',
            'amount': amount,
            'amount_display': amount_display,
            'deadline': deadline,
            'deadline_timestamp': deadline_timestamp,
            'source_url': url,
            'description': item.get('description', '')[:500] if item.get('description') else '',
            'tags': ['Hackathon', 'DoraHacks', 'Web3'],
            'geo_tags': ['Global', 'Online'],
            'type_tags': ['Hackathon'],
            'eligibility': {
                'gpa_min': None,
                'majors': [],
                'states': [],
                'citizenship': 'any',
                'grade_levels': []
            },
            'eligibility_text': 'Open to all developers globally',
            'source_type': 'dorahacks',
            'match_score': 50,
            'match_tier': 'Good',
            'verified': True,
            'last_verified': datetime.now().isoformat(),
            'priority_level': 'HIGH' if amount >= 10000 else 'MEDIUM'
        }
        
        opportunity_data['id'] = generate_opportunity_id(opportunity_data)
        return Scholarship(**opportunity_data)
        
    except Exception as e:
        logger.warning("DoraHacks transform failed", error=str(e))
        return None


# ========================================
# IMMUNEFI SCRAPER (Bug Bounties)
# ========================================
IMMUNEFI_API_URL = "https://immunefi.com/api/bounty"

async def fetch_immunefi_bounties() -> List[Dict[str, Any]]:
    """
    Fetch bug bounties from Immunefi using Sentinel Drone.
    """
    try:
        # Use fetch_content to bypass Cloudflare
        url = "https://immunefi.com/api/bounty/all"
        content = await crawler_service.fetch_content(url)
        
        if content:
             import re
             pre_match = re.search(r'<pre[^>]*>(.*?)</pre>', content, re.DOTALL)
             json_text = pre_match.group(1) if pre_match else content
             
             start = json_text.find('[')
             end = json_text.rfind(']')
             if start != -1 and end != -1:
                 try:
                     data = json.loads(json_text[start:end+1])
                     bounties = data if isinstance(data, list) else data.get('data', [])
                     logger.info("Immunefi API success", count=len(bounties))
                     return bounties[:100]
                 except:
                     pass
        
        # Fallback: Try explore page parsing if API fails
        # Use crawler_service on main page
        content2 = await crawler_service.fetch_content("https://immunefi.com/explore/")
        if content2:
            match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', content2)
            if match:
                page_data = json.loads(match.group(1))
                bounties = page_data.get('props', {}).get('pageProps', {}).get('bounties', [])
                logger.info("Immunefi page parse success", count=len(bounties))
                return bounties[:100]
                    
    except Exception as e:
        logger.warning("Immunefi fetch failed", error=str(e))
    
    return []


def transform_immunefi_bounty(item: Dict[str, Any]) -> Optional[Scholarship]:
    """Transform Immunefi bounty to Scholarship model"""
    try:
        title = item.get('name', '') or item.get('project', '')
        slug = item.get('slug', '') or item.get('id', '')
        
        if not title:
            return None
        
        url = f"https://immunefi.com/bounty/{slug}/" if slug else item.get('url', '')
        
        # Parse max bounty reward
        amount = 0
        max_bounty = item.get('maxBounty') or item.get('max_bounty') or 0
        try:
            amount = int(float(str(max_bounty).replace(',', '').replace('$', '')))
        except:
            pass
        
        amount_display = f"Up to ${amount:,}" if amount > 0 else "Varies"
        
        opportunity_data = {
            'id': '',
            'name': f"{title} Bug Bounty",
            'title': f"{title} Bug Bounty",
            'organization': title,
            'amount': amount,
            'amount_display': amount_display,
            'deadline': None,  # Bug bounties typically don't have deadlines
            'deadline_timestamp': None,
            'source_url': url,
            'description': f"Bug bounty program for {title}. Find vulnerabilities and get rewarded.",
            'tags': ['Bug Bounty', 'Immunefi', 'Security', 'Web3'],
            'geo_tags': ['Global', 'Remote'],
            'type_tags': ['Bounty'],
            'eligibility': {
                'gpa_min': None,
                'majors': [],
                'states': [],
                'citizenship': 'any',
                'grade_levels': []
            },
            'eligibility_text': 'Open to security researchers globally',
            'source_type': 'immunefi',
            'match_score': 50,
            'match_tier': 'Good',
            'verified': True,
            'last_verified': datetime.now().isoformat(),
            'priority_level': 'HIGH' if amount >= 50000 else 'MEDIUM'
        }
        
        opportunity_data['id'] = generate_opportunity_id(opportunity_data)
        return Scholarship(**opportunity_data)
        
    except Exception as e:
        logger.warning("Immunefi transform failed", error=str(e))
        return None


# ========================================
# SUPERTEAM EARN SCRAPER
# ========================================
async def fetch_superteam_bounties() -> List[Dict[str, Any]]:
    """
    Fetch bounties from Superteam Earn.
    """
    try:
        # Superteam API usually works with httpx, but let's be safe
        url = "https://earn.superteam.fun/api/listings?type=bounty&status=open"
        content = await crawler_service.fetch_content(url)
        
        if content:
             import re
             pre_match = re.search(r'<pre[^>]*>(.*?)</pre>', content, re.DOTALL)
             json_text = pre_match.group(1) if pre_match else content
             
             
             # Check for list or object
             start_list = json_text.find('[')
             start_obj = json_text.find('{')
             
             if start_list != -1 and (start_obj == -1 or start_list < start_obj):
                 # It's a list
                 end = json_text.rfind(']')
                 if end != -1:
                     try:
                         data = json.loads(json_text[start_list:end+1])
                         logger.info("Superteam API success (list)", count=len(data))
                         return data[:50]
                     except:
                         pass
             
             elif start_obj != -1:
                 # It's an object
                 end = json_text.rfind('}')
                 if end != -1:
                     try:
                         data = json.loads(json_text[start_obj:end+1])
                         bounties = data if isinstance(data, list) else data.get('bounties', data.get('data', []))
                         logger.info("Superteam API success (object)", count=len(bounties))
                         return bounties[:50]
                     except:
                         pass
        
        # Fallback: Frontend Scrape
        logger.info("Superteam API format not found, attempting frontend scrape...")
        frontend_url = "https://earn.superteam.fun/bounties"
        html = await crawler_service.fetch_content(frontend_url)
        if html:
             match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
             if match:
                try:
                    data = json.loads(match.group(1))
                    # Superteam usually has props.pageProps.bounties or similar
                    # Recursive search again
                    def find_bounties(obj):
                        found = []
                        if isinstance(obj, dict):
                            if 'rewardAmount' in obj and 'slug' in obj:
                                found.append(obj)
                            for k, v in obj.items():
                                found.extend(find_bounties(v))
                        elif isinstance(obj, list):
                            for item in obj:
                                found.extend(find_bounties(item))
                        return found
                    
                    bounties = find_bounties(data)
                    unique = {b['slug']: b for b in bounties}.values()
                    if unique:
                         logger.info("Superteam frontend scrape success", count=len(unique))
                         return list(unique)
                except:
                    pass

    except Exception as e:
        logger.warning("Superteam fetch failed", error=str(e))
    
    return []


def transform_superteam_bounty(item: Dict[str, Any]) -> Optional[Scholarship]:
    """
    Transform Superteam bounty to Scholarship model.
    
    CRITICAL URL FIX (Bismillah, Alhamdulillah):
    After careful research based on user screenshots:
    
    BROKEN: https://earn.superteam.fun/listings/{slug}/  (404 "Nothing Found")
    WORKS:  https://earn.superteam.fun/listing/{slug}    (SINGULAR, no trailing slash!)
    
    The canonical public-facing URL is:
        https://earn.superteam.fun/listing/{slug}
    
    Note: "listing" is SINGULAR, NOT "listings" (plural)!
    """
    try:
        title = item.get('title', '') or item.get('name', '')

        # Prefer canonical URL if the API provides one
        raw_url = item.get('url') or item.get('link') or ''
        slug = item.get('slug', '') or item.get('listingSlug', '') or item.get('titleSlug', '')

        if not slug and raw_url:
            # Extract slug from URLs like /listings/<slug>, /listing/<slug>, /bounties/<slug>
            import re
            m = re.search(r"/((?:listings?|bounties|projects))/([^/]+)/?", str(raw_url))
            if m:
                slug = m.group(2)

        if not title:
            return None

        # CRITICAL: The canonical working URL format is /listing/{slug} (SINGULAR!)
        # NOT /listings/{slug} which leads to 404 "Nothing Found"
        if slug:
            url = f"https://earn.superteam.fun/listing/{slug}"
        elif raw_url and str(raw_url).startswith('http'):
            # Normalize any existing URL to the correct format
            url = str(raw_url).replace('/listings/', '/listing/').replace('/bounties/', '/listing/').rstrip('/')
        elif raw_url and str(raw_url).startswith('/'):
            path = str(raw_url).replace('/listings/', '/listing/').replace('/bounties/', '/listing/').rstrip('/')
            url = f"https://earn.superteam.fun{path}"
        else:
            # No reliable URL → omit link (better than broken 404)
            url = ''
        
        # Parse reward
        amount = 0
        reward = item.get('rewardAmount') or item.get('reward') or item.get('usdValue') or 0
        try:
            amount = int(float(str(reward).replace(',', '')))
        except:
            pass
        
        token = item.get('token', 'USDC')
        amount_display = f"${amount:,}" if token in ['USDC', 'USD'] else f"{amount:,} {token}"
        
        # Parse deadline
        deadline = None
        deadline_timestamp = None
        end_date = item.get('deadline') or item.get('endDate')
        if end_date:
            try:
                deadline_dt = datetime.fromisoformat(str(end_date).replace('Z', '+00:00'))
                deadline = deadline_dt.strftime('%Y-%m-%d')
                deadline_timestamp = int(deadline_dt.timestamp())
            except:
                pass
        
        opportunity_data = {
            'id': '',
            'name': title,
            'title': title,
            'organization': item.get('sponsor', {}).get('name', 'Superteam') if isinstance(item.get('sponsor'), dict) else 'Superteam',
            'amount': amount,
            'amount_display': amount_display,
            'deadline': deadline,
            'deadline_timestamp': deadline_timestamp,
            'source_url': url,
            'description': item.get('description', '')[:500] if item.get('description') else '',
            'tags': ['Bounty', 'Superteam', 'Solana', 'Web3'],
            'geo_tags': ['Global', 'Remote'],
            'type_tags': ['Bounty'],
            'eligibility': {
                'gpa_min': None,
                'majors': [],
                'states': [],
                'citizenship': 'any',
                'grade_levels': []
            },
            'eligibility_text': 'Open to Solana developers and creators',
            'source_type': 'superteam',
            'match_score': 50,
            'match_tier': 'Good',
            'verified': True,
            'last_verified': datetime.now().isoformat(),
            'priority_level': 'HIGH' if amount >= 1000 else 'MEDIUM'
        }
        
        opportunity_data['id'] = generate_opportunity_id(opportunity_data)
        return Scholarship(**opportunity_data)
        
    except Exception as e:
        logger.warning("Superteam transform failed", error=str(e))
        return None


# ========================================
# GITCOIN SCRAPER
# ========================================
async def fetch_gitcoin_bounties() -> List[Dict[str, Any]]:
    """Fetch bounties/grants from Gitcoin"""
    try:
        url = "https://gitcoin.co/api/v0.1/grants/?page=1&limit=50"
        content = await crawler_service.fetch_content(url)
        
        if content:
             import re
             pre_match = re.search(r'<pre[^>]*>(.*?)</pre>', content, re.DOTALL)
             json_text = pre_match.group(1) if pre_match else content
             
             start = json_text.find('{')
             end = json_text.rfind('}')
             if start != -1 and end != -1:
                 try:
                     data = json.loads(json_text[start:end+1])
                     grants = data if isinstance(data, list) else data.get('results', data.get('grants', []))
                     logger.info("Gitcoin API success", count=len(grants))
                     return grants[:50]
                 except:
                     pass
                
    except Exception as e:
        logger.warning("Gitcoin fetch failed", error=str(e))
    
    return []


def transform_gitcoin_grant(item: Dict[str, Any]) -> Optional[Scholarship]:
    """Transform Gitcoin grant to Scholarship model"""
    try:
        title = item.get('title', '') or item.get('name', '')
        
        if not title:
            return None
        
        url = item.get('url', '') or f"https://gitcoin.co/grants/{item.get('id', '')}"
        
        amount = int(item.get('amount_received', 0) or 0)
        
        opportunity_data = {
            'id': '',
            'name': title,
            'title': title,
            'organization': 'Gitcoin',
            'amount': amount,
            'amount_display': f"${amount:,}" if amount > 0 else "Varies",
            'deadline': None,
            'deadline_timestamp': None,
            'source_url': url,
            'description': item.get('description', '')[:500] if item.get('description') else '',
            'tags': ['Grant', 'Gitcoin', 'Web3', 'Open Source'],
            'geo_tags': ['Global', 'Remote'],
            'type_tags': ['Grant'],
            'eligibility': {
                'gpa_min': None,
                'majors': [],
                'states': [],
                'citizenship': 'any',
                'grade_levels': []
            },
            'eligibility_text': 'Open to open-source developers',
            'source_type': 'gitcoin',
            'match_score': 50,
            'match_tier': 'Good',
            'verified': True,
            'last_verified': datetime.now().isoformat(),
            'priority_level': 'MEDIUM'
        }
        
        opportunity_data['id'] = generate_opportunity_id(opportunity_data)
        return Scholarship(**opportunity_data)
        
    except Exception as e:
        logger.warning("Gitcoin transform failed", error=str(e))
        return None


# ========================================
# KAGGLE COMPETITIONS SCRAPER
# ========================================
async def fetch_kaggle_competitions() -> List[Dict[str, Any]]:
    """
    Fetch active competitions from Kaggle.
    Kaggle has a public meta API for competition listings.
    """
    try:
        # Kaggle's public competition list API
        url = "https://www.kaggle.com/api/v1/competitions/list?search=&category=all&sortBy=latestDeadline&page=1&pageSize=50"
        
        # Try direct API first (may require no auth for public competitions)
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
            })
            
            if response.status_code == 200:
                data = response.json()
                competitions = data if isinstance(data, list) else data.get('competitions', [])
                logger.info("Kaggle API success", count=len(competitions))
                return competitions
        
        # Fallback: Scrape the competitions page
        logger.info("Kaggle API failed, trying frontend scrape...")
        html = await crawler_service.fetch_content("https://www.kaggle.com/competitions")
        
        if html:
            import re
            # Look for __NEXT_DATA__ or window.SSR_DATA patterns
            match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    # Navigate to competitions data
                    competitions = data.get('props', {}).get('pageProps', {}).get('competitions', [])
                    if competitions:
                        logger.info("Kaggle frontend scrape success", count=len(competitions))
                        return competitions
                except:
                    pass
                    
    except Exception as e:
        logger.warning("Kaggle fetch failed", error=str(e))
    
    # Static fallback with popular ongoing competitions
    return get_static_kaggle_competitions()


def get_static_kaggle_competitions() -> List[Dict[str, Any]]:
    """Static fallback for Kaggle when API/scraping fails"""
    return [
        {
            "title": "Titanic - Machine Learning from Disaster",
            "url": "https://www.kaggle.com/c/titanic",
            "deadline": None,
            "reward": "Knowledge",
            "category": "Getting Started"
        },
        {
            "title": "House Prices - Advanced Regression Techniques",
            "url": "https://www.kaggle.com/c/house-prices-advanced-regression-techniques",
            "deadline": None,
            "reward": "Knowledge",
            "category": "Getting Started"
        },
        {
            "title": "Digit Recognizer",
            "url": "https://www.kaggle.com/c/digit-recognizer",
            "deadline": None,
            "reward": "Knowledge",
            "category": "Getting Started"
        }
    ]


def transform_kaggle_competition(item: Dict[str, Any]) -> Optional[Scholarship]:
    """Transform Kaggle competition to Scholarship model"""
    try:
        title = item.get('title') or item.get('competitionTitle') or item.get('name', '')
        
        if not title:
            return None
        
        # URL construction
        slug = item.get('ref') or item.get('slug') or item.get('url', '')
        if slug and not slug.startswith('http'):
            url = f"https://www.kaggle.com/c/{slug}" if not slug.startswith('/') else f"https://www.kaggle.com{slug}"
        else:
            url = slug or f"https://www.kaggle.com/competitions"
        
        # Parse reward
        amount = 0
        reward = item.get('reward') or item.get('prize') or item.get('totalPrize', 'Knowledge')
        if isinstance(reward, str):
            # Clean "$50,000" → 50000
            import re
            match = re.search(r'[\$€]?([\d,]+)', reward.replace(',', ''))
            if match:
                try:
                    amount = int(match.group(1))
                except:
                    pass
        elif isinstance(reward, (int, float)):
            amount = int(reward)
        
        amount_display = f"${amount:,}" if amount > 0 else str(reward)
        
        # Parse deadline
        deadline = None
        deadline_timestamp = None
        deadline_str = item.get('deadline') or item.get('mergingDeadline')
        if deadline_str:
            try:
                deadline_dt = datetime.fromisoformat(str(deadline_str).replace('Z', '+00:00'))
                deadline = deadline_dt.strftime('%Y-%m-%d')
                deadline_timestamp = int(deadline_dt.timestamp())
            except:
                pass
        
        opportunity_data = {
            'id': '',
            'name': title,
            'title': title,
            'organization': 'Kaggle',
            'amount': amount,
            'amount_display': amount_display,
            'deadline': deadline,
            'deadline_timestamp': deadline_timestamp,
            'source_url': url,
            'description': item.get('description', '')[:500] if item.get('description') else f"Kaggle competition: {title}",
            'tags': ['Competition', 'Kaggle', 'Machine Learning', 'Data Science'],
            'geo_tags': ['Global', 'Online'],
            'type_tags': ['Competition'],
            'eligibility': {
                'gpa_min': None,
                'majors': [],
                'states': [],
                'citizenship': 'any',
                'grade_levels': []
            },
            'eligibility_text': 'Open to data scientists and ML practitioners globally',
            'source_type': 'kaggle',
            'match_score': 50,
            'match_tier': 'Good',
            'verified': True,
            'last_verified': datetime.now().isoformat(),
            'priority_level': 'HIGH' if amount >= 10000 else 'MEDIUM'
        }
        
        opportunity_data['id'] = generate_opportunity_id(opportunity_data)
        return Scholarship(**opportunity_data)
        
    except Exception as e:
        logger.warning("Kaggle transform failed", error=str(e))
        return None


# ========================================
# LEETCODE CONTESTS SCRAPER
# ========================================
async def fetch_leetcode_contests() -> List[Dict[str, Any]]:
    """
    Fetch upcoming LeetCode contests.
    LeetCode has a GraphQL API for contest listings.
    """
    try:
        # LeetCode GraphQL endpoint
        url = "https://leetcode.com/graphql"
        
        query = """
        query {
            allContests {
                title
                titleSlug
                startTime
                duration
                description
            }
        }
        """
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                json={"query": query},
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                contests = data.get('data', {}).get('allContests', [])
                # Filter to upcoming contests only
                now = datetime.now().timestamp()
                upcoming = [c for c in contests if c.get('startTime', 0) > now]
                logger.info("LeetCode API success", count=len(upcoming))
                return upcoming[:20]  # Limit to 20 upcoming
                
    except Exception as e:
        logger.warning("LeetCode fetch failed", error=str(e))
    
    return get_static_leetcode_contests()


def get_static_leetcode_contests() -> List[Dict[str, Any]]:
    """Static fallback for LeetCode contests"""
    return [
        {
            "title": "Weekly Contest",
            "titleSlug": "weekly-contest",
            "description": "Weekly LeetCode programming contest",
            "recurring": True
        },
        {
            "title": "Biweekly Contest",
            "titleSlug": "biweekly-contest",
            "description": "Biweekly LeetCode programming contest",
            "recurring": True
        }
    ]


def transform_leetcode_contest(item: Dict[str, Any]) -> Optional[Scholarship]:
    """Transform LeetCode contest to Scholarship model"""
    try:
        title = item.get('title', '')
        slug = item.get('titleSlug', '')
        
        if not title:
            return None
        
        url = f"https://leetcode.com/contest/{slug}/" if slug else "https://leetcode.com/contest/"
        
        # Parse start time as deadline
        deadline = None
        deadline_timestamp = None
        start_time = item.get('startTime')
        if start_time:
            try:
                deadline_dt = datetime.fromtimestamp(start_time)
                deadline = deadline_dt.strftime('%Y-%m-%d %H:%M')
                deadline_timestamp = int(start_time)
            except:
                pass
        
        opportunity_data = {
            'id': '',
            'name': title,
            'title': title,
            'organization': 'LeetCode',
            'amount': 0,
            'amount_display': 'Prizes + Rankings',
            'deadline': deadline,
            'deadline_timestamp': deadline_timestamp,
            'source_url': url,
            'description': item.get('description', '') or f"Compete in {title} on LeetCode. Improve your ranking and problem-solving skills.",
            'tags': ['Contest', 'LeetCode', 'Competitive Programming', 'Algorithms'],
            'geo_tags': ['Global', 'Online'],
            'type_tags': ['Competition'],
            'eligibility': {
                'gpa_min': None,
                'majors': [],
                'states': [],
                'citizenship': 'any',
                'grade_levels': []
            },
            'eligibility_text': 'Open to all programmers globally',
            'source_type': 'leetcode',
            'match_score': 50,
            'match_tier': 'Good',
            'verified': True,
            'last_verified': datetime.now().isoformat(),
            'priority_level': 'MEDIUM'
        }
        
        opportunity_data['id'] = generate_opportunity_id(opportunity_data)
        return Scholarship(**opportunity_data)
        
    except Exception as e:
        logger.warning("LeetCode transform failed", error=str(e))
        return None


# ========================================
# MASTER SCRAPER FUNCTION
# ========================================
async def scrape_all_platforms() -> Dict[str, int]:
    """
    Scrape all platforms and return counts per platform.
    """
    logger.info("Starting multi-platform scrape...")
    results = {
        'dorahacks_hackathons': 0,
        'dorahacks_bounties': 0,
        'immunefi': 0,
        'superteam': 0,
        'gitcoin': 0,
        'kaggle': 0,
        'leetcode': 0,
        'total': 0
    }
    
    all_scholarships = []
    
    # DoraHacks Hackathons
    try:
        dh_hackathons = await fetch_dorahacks_hackathons()
        for item in dh_hackathons:
            s = transform_dorahacks_hackathon(item)
            if s:
                all_scholarships.append(s)
                results['dorahacks_hackathons'] += 1
    except Exception as e:
        logger.warning("DoraHacks hackathons scrape error", error=str(e))
        import traceback
        traceback.print_exc()
    
    # DoraHacks Bounties
    try:
        dh_bounties = await fetch_dorahacks_bounties()
        for item in dh_bounties:
            s = transform_dorahacks_hackathon(item)  # Same structure
            if s:
                s.tags = ['Bounty', 'DoraHacks', 'Web3']
                s.type_tags = ['Bounty']
                all_scholarships.append(s)
                results['dorahacks_bounties'] += 1
    except Exception as e:
        logger.warning("DoraHacks bounties scrape error", error=str(e))
    
    # Immunefi
    try:
        immunefi_bounties = await fetch_immunefi_bounties()
        for item in immunefi_bounties:
            s = transform_immunefi_bounty(item)
            if s:
                all_scholarships.append(s)
                results['immunefi'] += 1
    except Exception as e:
        logger.warning("Immunefi scrape error", error=str(e))
    
    # Superteam
    try:
        superteam_bounties = await fetch_superteam_bounties()
        for item in superteam_bounties:
            s = transform_superteam_bounty(item)
            if s:
                all_scholarships.append(s)
                results['superteam'] += 1
    except Exception as e:
        logger.warning("Superteam scrape error", error=str(e))
        import traceback
        traceback.print_exc()
    
    # Gitcoin
    try:
        gitcoin_grants = await fetch_gitcoin_bounties()
        for item in gitcoin_grants:
            s = transform_gitcoin_grant(item)
            if s:
                all_scholarships.append(s)
                results['gitcoin'] += 1
    except Exception as e:
        logger.warning("Gitcoin scrape error", error=str(e))
    
    # Kaggle Competitions
    try:
        kaggle_competitions = await fetch_kaggle_competitions()
        for item in kaggle_competitions:
            s = transform_kaggle_competition(item)
            if s:
                all_scholarships.append(s)
                results['kaggle'] += 1
    except Exception as e:
        logger.warning("Kaggle scrape error", error=str(e))
    
    # LeetCode Contests
    try:
        leetcode_contests = await fetch_leetcode_contests()
        for item in leetcode_contests:
            s = transform_leetcode_contest(item)
            if s:
                all_scholarships.append(s)
                results['leetcode'] += 1
    except Exception as e:
        logger.warning("LeetCode scrape error", error=str(e))
    
    results['total'] = len(all_scholarships)
    logger.info("Multi-platform scrape complete", **results)
    
    return results, all_scholarships


async def populate_database_multi_platform() -> Dict[str, int]:
    """
    Scrape all platforms and save to Firestore.
    """
    logger.info("Populating database from multiple platforms...")
    
    results, scholarships = await scrape_all_platforms()
    
    saved_count = 0
    for scholarship in scholarships:
        try:
            await db.save_scholarship(scholarship)
            saved_count += 1
        except Exception as e:
            logger.warning("Failed to save scholarship", id=scholarship.id, error=str(e))
            continue
    
    results['saved'] = saved_count
    logger.info("Multi-platform population complete", **results)
    return results


# CLI usage
if __name__ == "__main__":
    async def main():
        results, scholarships = await scrape_all_platforms()
        print(f"\n=== Multi-Platform Scrape Results ===")
        for platform, count in results.items():
            print(f"  {platform}: {count}")
        
        print(f"\nSample opportunities:")
        for s in scholarships[:10]:
            print(f"  - [{s.source_type}] {s.name}: {s.amount_display}")
            print(f"    URL: {s.source_url}")
    
    asyncio.run(main())
