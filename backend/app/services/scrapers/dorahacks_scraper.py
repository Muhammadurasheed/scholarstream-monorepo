"""
DoraHacks Deep Scraper
Specialized scraper that navigates to individual hackathon detail pages
to extract accurate prize pools and deadlines.
"""
import asyncio
import re
import hashlib
import structlog
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser

from app.database import db
from app.models import Scholarship
from app.services.flink_processor import generate_opportunity_id
from app.services.kafka_config import KafkaConfig, kafka_producer_manager

logger = structlog.get_logger()


class DoraHacksDeepScraper:
    """
    Deep scraper for DoraHacks that:
    1. Crawls the hackathon list page to find all hackathon URLs
    2. Visits each detail page to extract accurate prize pools and deadlines
    3. Publishes enriched data to the Kafka stream
    """
    
    BASE_URL = "https://dorahacks.io"
    LIST_URL = "https://dorahacks.io/hackathon"
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        
    async def initialize(self):
        """Initialize Playwright browser with stealth settings"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        logger.info("DoraHacks Deep Scraper initialized")
        
    async def shutdown(self):
        """Clean shutdown of browser"""
        if self.browser:
            await self.browser.close()
            logger.info("DoraHacks Deep Scraper shutdown complete")
    
    async def _create_stealth_context(self):
        """Create a browser context with stealth settings"""
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
        )
        return context
    
    async def get_hackathon_urls(self, page: Page, max_count: int = 20) -> List[str]:
        """Extract hackathon URLs from the list page"""
        await page.goto(self.LIST_URL, wait_until='networkidle', timeout=60000)
        await asyncio.sleep(3)  # Wait for Vue.js to render
        
        # Scroll to load more items
        for _ in range(3):
            await page.evaluate("window.scrollBy(0, 1000)")
            await asyncio.sleep(1)
        
        # Extract hackathon links
        links = await page.query_selector_all('a[href^="/hackathon/"]')
        urls = set()
        
        for link in links:
            href = await link.get_attribute('href')
            if href and '/hackathon/' in href:
                # Filter out non-hackathon pages like /hackathon/list
                parts = href.split('/')
                if len(parts) >= 3 and parts[2] and parts[2] not in ['list', 'create', '']:
                    full_url = f"{self.BASE_URL}{href}"
                    urls.add(full_url)
                    
        hackathon_urls = list(urls)[:max_count]
        logger.info(f"Found {len(hackathon_urls)} hackathon URLs to deep scrape")
        return hackathon_urls
    
    async def extract_hackathon_details(self, page: Page, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract prize pool and deadline from a hackathon detail page.
        Returns structured opportunity data.
        """
        try:
            await page.goto(url, wait_until='networkidle', timeout=45000)
            await asyncio.sleep(2)  # Wait for content to render
            
            # Get page content
            content = await page.content()
            title = await page.title()
            
            # Extract hackathon name from title (usually "Name | DoraHacks")
            hackathon_name = title.split('|')[0].strip() if '|' in title else title
            
            # V3 FIX: Surgical prize extraction - inspect page structure directly
            prize_amount = 0
            prize_display = "View Prize Details →"
            
            # STRATEGY 1: Look for structured prize elements first (most reliable)
            try:
                # DoraHacks uses specific class patterns for prize display
                prize_selectors = [
                    '.prize-pool', '.prize-amount', '.total-prize',
                    '[class*="prize"]', '[class*="reward"]', '[class*="bounty"]',
                    '.hackathon-info .amount', '.buidl-header .prize'
                ]
                for selector in prize_selectors:
                    elem = await page.query_selector(selector)
                    if elem:
                        text = await elem.inner_text()
                        # Extract number from text like "$50,000" or "50,000 USDC"
                        num_match = re.search(r'[\$]?([\d,]+(?:\.\d+)?)\s*(?:K|k)?', text)
                        if num_match:
                            val = float(num_match.group(1).replace(',', ''))
                            if 'k' in text.lower() and val < 10000:
                                val *= 1000
                            if val >= 100:  # Minimum $100 prize to be valid
                                prize_amount = val
                                prize_display = f"${prize_amount:,.0f}"
                                logger.info(f"Prize from element: {prize_display}")
                                break
            except Exception as e:
                logger.debug(f"Element-based prize extraction failed: {e}")
            
            # STRATEGY 2: Regex patterns on full page content
            if prize_amount == 0:
                prize_patterns = [
                    # Strongest patterns first - explicit "Prize Pool"
                    r'(?:Prize\s*Pool|Total\s*Prize|Bounty\s*Pool)[:\s]*\$?([\d,]+(?:\.\d+)?)\s*([Kk])?\s*(?:USD|USDC|USDT)?',
                    # Dollar amount followed by prize context
                    r'\$([\d,]+(?:\.\d+)?)\s*([Kk])?\s*(?:in\s*)?(?:prizes?|pool|bounty|bounties|rewards?)',
                    # Number followed by currency then prize context  
                    r'([\d,]+(?:\.\d+)?)\s*([Kk])?\s*(?:USD|USDC|USDT)\s*(?:Prize|Pool|Bounty|Reward)',
                    # "up to $X" pattern
                    r'up\s*to\s*\$?([\d,]+(?:\.\d+)?)\s*([Kk])?',
                    # Standalone large dollar amounts (likely prize)
                    r'(?:^|\s)\$([\d,]+(?:\.\d+)?)\s*([Kk])?(?:\s|$)',
                ]
                
                for pattern in prize_patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        amount_str = match.group(1).replace(',', '')
                        try:
                            val = float(amount_str)
                            # Handle K suffix
                            has_k = match.group(2) is not None if len(match.groups()) > 1 else False
                            if has_k and val < 10000:
                                val *= 1000
                            if val >= 100:  # Minimum threshold
                                prize_amount = val
                                prize_display = f"${prize_amount:,.0f}"
                                logger.info(f"Prize from regex: {prize_display} using pattern {pattern[:30]}")
                                break
                        except ValueError:
                            continue
            
            # STRATEGY 3: Crypto amounts as fallback
            if prize_amount == 0:
                crypto_patterns = [
                    r'([\d,]+(?:\.\d+)?)\s*([Kk])?\s*(?:ETH|SOL|USDC|USDT|DAI|BTC)',
                    r'([\d,]+(?:\.\d+)?)\s*([Kk])?\s*tokens?\s*(?:prize|reward|bounty)?',
                ]
                for pattern in crypto_patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        amount_str = match.group(1).replace(',', '')
                        try:
                            val = float(amount_str)
                            has_k = match.group(2) is not None if len(match.groups()) > 1 else False
                            if has_k and val < 10000:
                                val *= 1000
                            if val > 0:
                                prize_display = f"{val:,.0f}+ in crypto"
                                logger.info(f"Crypto prize: {prize_display}")
                                break
                        except ValueError:
                            continue
            
            # Strategy 2: Try clicking on "Important Dates" tab and extracting deadline
            deadline = None
            deadline_timestamp = None
            
            try:
                # First look for deadline in page content
                deadline_patterns = [
                    r'(?:Submission|Registration|Application)\s*Deadline[:\s]*([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
                    r'Ends?\s*(?:on|:)?\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
                    r'Due[:\s]*([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
                    r'(\d{4}-\d{2}-\d{2})',  # ISO format
                ]
                
                for pattern in deadline_patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        date_str = match.group(1)
                        try:
                            # Try multiple date formats
                            for fmt in ['%B %d, %Y', '%B %d %Y', '%Y-%m-%d', '%b %d, %Y']:
                                try:
                                    parsed_date = datetime.strptime(date_str.strip(), fmt)
                                    deadline = parsed_date.strftime('%Y-%m-%d')
                                    deadline_timestamp = int(parsed_date.timestamp())
                                    logger.debug(f"Extracted deadline: {deadline} from {url}")
                                    break
                                except ValueError:
                                    continue
                            if deadline:
                                break
                        except Exception:
                            continue
            except Exception as e:
                logger.debug(f"Could not extract deadline: {e}")
            
            # Extract organization/sponsor
            organization = "DoraHacks"
            org_patterns = [
                r'(?:Organized|Hosted|Sponsored)\s*by[:\s]*([A-Za-z0-9\s&]+)',
                r'by\s+([A-Za-z0-9]+)\s+(?:and|&)',
            ]
            for pattern in org_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    organization = match.group(1).strip()[:50]  # Limit length
                    break
            
            # Extract description (first 500 chars of main content)
            description = ""
            try:
                desc_elem = await page.query_selector('.markdown, .description, [class*="desc"]')
                if desc_elem:
                    description = await desc_elem.inner_text()
                    description = description[:500].strip()
            except:
                pass
            
            # Build opportunity data
            opportunity = {
                "title": hackathon_name,
                "name": hackathon_name,
                "organization": organization,
                "amount": prize_amount,
                "amount_display": prize_display,
                "deadline": deadline,
                "deadline_timestamp": deadline_timestamp,
                "description": description or f"Hackathon hosted on DoraHacks",
                "source_url": url,
                "url": url,
                "type_tags": ["Hackathon", "Web3"],
                "geo_tags": ["Global", "Remote"],
                "eligibility_text": "Open to all developers",
                "source_type": "dorahacks",
            }
            
            logger.info(f"Extracted: {hackathon_name} | Prize: {prize_display} | Deadline: {deadline or 'TBD'}")
            return opportunity
            
        except Exception as e:
            logger.error(f"Failed to extract from {url}: {e}")
            return None
    
    async def deep_scrape(self, max_hackathons: int = 15) -> List[Dict[str, Any]]:
        """
        Main entry point: Deep scrape DoraHacks hackathons.
        Returns list of fully enriched opportunity dicts.
        """
        if not self.browser:
            await self.initialize()
        
        context = await self._create_stealth_context()
        page = await context.new_page()
        
        try:
            # Step 1: Get hackathon URLs from list page
            hackathon_urls = await self.get_hackathon_urls(page, max_count=max_hackathons)
            
            # Step 2: Visit each detail page and extract data
            opportunities = []
            for i, url in enumerate(hackathon_urls):
                try:
                    logger.info(f"Deep scraping [{i+1}/{len(hackathon_urls)}]: {url[:60]}...")
                    
                    opportunity = await self.extract_hackathon_details(page, url)
                    if opportunity and opportunity.get('title'):
                        title_safe = opportunity['title'].encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)

                        # Generate consistent stable ID (align with the rest of the platform)
                        stable_id = generate_opportunity_id({
                            'url': opportunity.get('url') or opportunity.get('source_url') or url,
                            'name': opportunity.get('title') or opportunity.get('name'),
                            'organization': opportunity.get('organization') or 'DoraHacks'
                        })
                        opportunity['id'] = stable_id
                        opportunities.append(opportunity)

                        # DIRECT SAVE to Firestore (immediate availability)
                        try:
                            scholarship = Scholarship(
                                id=stable_id,
                                name=opportunity['title'],
                                title=opportunity['title'],
                                organization=opportunity['organization'],
                                amount=opportunity['amount'],
                                amount_display=opportunity['amount_display'],
                                deadline=opportunity['deadline'],
                                deadline_timestamp=opportunity.get('deadline_timestamp'),
                                description=opportunity['description'],
                                url=opportunity['url'],
                                source_url=opportunity['source_url'],
                                tags=opportunity['type_tags'] + opportunity['geo_tags'],
                                type=opportunity['type_tags'][0] if opportunity['type_tags'] else "Hackathon",
                                eligibility_text=opportunity['eligibility_text'],
                                match_score=0.0,  # Rely on real-time matching
                            )
                            await db.save_scholarship(scholarship)
                            logger.info(f"Directly saved to DB: {title_safe}")
                        except Exception as db_err:
                            logger.error(f"Failed direct DB save for {url}: {db_err}")

                        # Still publish to Kafka stream for other workers (e.g. vectorization)
                        kafka_producer_manager.publish_to_stream(
                            topic=KafkaConfig.TOPIC_RAW_HTML,
                            key=url,
                            value={
                                "url": url,
                                "html": f"<opportunity>{opportunity}</opportunity>",  # Structured data
                                "source": "dorahacks_deep",
                                "extracted_data": opportunity,  # Direct pass-through
                            }
                        )
                except Exception as e:
                    logger.error(f"Failed to extract from {url}: {str(e).encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)}")
                
                # Rate limiting - be gentle with DoraHacks
                await asyncio.sleep(1.5)
            
            logger.info(f"DoraHacks deep scrape complete: {len(opportunities)} opportunities extracted")
            return opportunities
            
        finally:
            await context.close()


# Global instance
dorahacks_scraper = DoraHacksDeepScraper()


async def run_dorahacks_deep_scrape(max_hackathons: int = 15) -> List[Dict[str, Any]]:
    """Convenience function to run deep scrape"""
    scraper = DoraHacksDeepScraper()
    try:
        await scraper.initialize()
        return await scraper.deep_scrape(max_hackathons)
    finally:
        await scraper.shutdown()
