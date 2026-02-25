"""
DevPost Deep Scraper
Specialized scraper that navigates to individual DevPost hackathon pages
to ensure canonical subdomain URLs and accurate detail extraction.
"""
import asyncio
import re
import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser

from app.database import db
from app.models import Scholarship
from app.services.flink_processor import generate_opportunity_id


logger = structlog.get_logger()


class DevPostDeepScraper:
    """
    Deep scraper for DevPost that:
    1. Crawls the hackathon list page
    2. Extracts the specific subdomain URLs (e.g., xxx.devpost.com)
    3. Visits pages for metadata verification
    4. Saves to Firestore
    """
    
    BASE_URL = "https://devpost.com"
    LIST_URL = "https://devpost.com/hackathons"
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        
    async def initialize(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        logger.info("DevPost Deep Scraper initialized")
        
    async def shutdown(self):
        if self.browser:
            await self.browser.close()
    
    async def _create_stealth_context(self):
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        return context
    
    async def get_hackathon_urls(self, page: Page, max_count: int = 30) -> List[str]:
        """Extract hackathon URLs, prioritizing subdomains"""
        await page.goto(self.LIST_URL, wait_until='networkidle', timeout=60000)
        await asyncio.sleep(4)
        
        # Scroll to trigger lazy loading
        for _ in range(3):
            await page.evaluate("window.scrollBy(0, 1000)")
            await asyncio.sleep(1)
            
        links = await page.query_selector_all('a[href*="devpost.com"]')
        urls = set()
        
        for link in links:
            href = await link.get_attribute('href')
            if href:
                # We want https://slug.devpost.com/ 
                # OR https://devpost.com/hackathons/slug (which we will normalize)
                if 'devpost.com' in href:
                    # Filter out generic links
                    if any(x in href for x in ['/hackathons', '/software', '/teams', '/help']):
                        # If it's a specific hackathon path
                        m = re.search(r'devpost\.com/hackathons/([a-zA-Z0-9_-]+)', href)
                        if m:
                            urls.add(f"https://{m.group(1)}.devpost.com/")
                        continue
                    
                    # If it's already a subdomain format
                    if '.devpost.com' in href and 'www.' not in href:
                        # Clean to base URL
                        match = re.search(r'https?://([a-zA-Z0-9_-]+\.devpost\.com)/?', href)
                        if match:
                            urls.add(f"https://{match.group(1)}/")
                            
        hackathon_urls = list(urls)[:max_count]
        logger.info(f"Found {len(hackathon_urls)} DevPost subdomain URLs")
        return hackathon_urls

    async def extract_details(self, page: Page, url: str) -> Optional[Dict[str, Any]]:
        """Deep extract from the individual hackathon page"""
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(2)
            
            title = await page.title()
            name = title.split('|')[0].strip()
            
            # Extract Organization (Partner)
            org_elem = await page.query_selector('.host-name, .partner-logo img')
            organization = "DevPost"
            if org_elem:
                if await org_elem.get_attribute('alt'):
                    organization = await org_elem.get_attribute('alt')
                else:
                    organization = await org_elem.inner_text()

            # Prize
            prize_amount = 0
            prize_display = "Varies"
            prize_elem = await page.query_selector('.total-prizes')
            if prize_elem:
                text = await prize_elem.inner_text()
                num_match = re.search(r'\$?([\d,]+)', text)
                if num_match:
                    prize_amount = float(num_match.group(1).replace(',', ''))
                    prize_display = f"${prize_amount:,.0f}"

            # Deadline — extract and parse robustly
            deadline = None
            deadline_ts = None
            
            # Check for "This hackathon has ended" banner first
            ended_elem = await page.query_selector('.status-label, .ended-banner, [class*="ended"]')
            if ended_elem:
                ended_text = await ended_elem.inner_text()
                if 'ended' in ended_text.lower() or 'closed' in ended_text.lower():
                    logger.info(f"Skipping ended hackathon: {name}")
                    return None
            
            # Check the schedule sidebar for dates
            schedule_elem = await page.query_selector('#challenge-sidebar time, .challenge-info time, time[datetime]')
            if schedule_elem:
                raw_dt = await schedule_elem.get_attribute('datetime')
                if raw_dt:
                    try:
                        from dateutil import parser as dateparser
                        parsed = dateparser.parse(raw_dt)
                        if parsed and parsed < datetime.now(parsed.tzinfo or None):
                            logger.info(f"Skipping expired hackathon: {name} (deadline: {raw_dt})")
                            return None
                        deadline = parsed.isoformat() if parsed else None
                        deadline_ts = int(parsed.timestamp()) if parsed else None
                    except Exception:
                        pass
            
            # Fallback: try .submission-deadline text
            if not deadline:
                deadline_elem = await page.query_selector('.submission-deadline')
                if deadline_elem:
                    raw_deadline = await deadline_elem.inner_text()
                    try:
                        from dateutil import parser as dateparser
                        # Extract date from text like "Submission deadline: Jan 30, 2025"
                        cleaned = raw_deadline.replace('Submission deadline:', '').replace('Deadline:', '').strip()
                        parsed = dateparser.parse(cleaned)
                        if parsed:
                            if parsed < datetime.now(parsed.tzinfo or None):
                                logger.info(f"Skipping expired hackathon: {name} (deadline: {cleaned})")
                                return None
                            deadline = parsed.isoformat()
                            deadline_ts = int(parsed.timestamp())
                    except Exception:
                        pass

            return {
                "name": name,
                "organization": organization,
                "amount": prize_amount,
                "amount_display": prize_display,
                "deadline": deadline,
                "deadline_timestamp": deadline_ts,
                "url": url,
                "description": f"Hackathon hosted on DevPost by {organization}",
                "source_type": "devpost"
            }
        except Exception as e:
            logger.error(f"DevPost deep extract failed for {url}: {e}")
            return None

    async def run(self, max_items: int = 20):
        if not self.browser: await self.initialize()
        context = await self._create_stealth_context()
        page = await context.new_page()
        
        try:
            urls = await self.get_hackathon_urls(page, max_count=max_items)
            for url in urls:
                data = await self.extract_details(page, url)
                if data:
                    stable_id = generate_opportunity_id({
                        'url': data['url'],
                        'name': data['name'],
                        'organization': data['organization']
                    })
                    
                    scholarship = Scholarship(
                        id=stable_id,
                        name=data['name'],
                        title=data['name'],
                        organization=data['organization'],
                        amount=data['amount'],
                        amount_display=data['amount_display'],
                        url=data['url'],
                        source_url=data['url'],
                        description=data['description'],
                        tags=["Hackathon", "DevPost", "Tech"],
                        type="Hackathon",
                        verified=True,
                        last_verified=datetime.now().isoformat(),
                        source_type="devpost",
                        match_score=0.0
                    )
                    await db.save_scholarship(scholarship)
                    logger.info(f"Saved DevPost Deep Item: {data['name']}")
                    await asyncio.sleep(1)
        finally:
            await context.close()

async def populate_database_with_devpost_deep() -> int:
    scraper = DevPostDeepScraper()
    try:
        await scraper.initialize()
        await scraper.run(max_items=15)
        return 15
    finally:
        await scraper.shutdown()

if __name__ == "__main__":
    asyncio.run(populate_database_with_devpost_deep())
