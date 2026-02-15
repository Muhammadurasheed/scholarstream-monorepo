
import httpx
import asyncio
import structlog
from typing import List, Dict, Any, Optional
import time

from app.services.kafka_config import KafkaConfig, kafka_producer_manager

logger = structlog.get_logger()


from playwright.async_api import async_playwright, BrowserContext, Page
import random

class UniversalCrawlerService:
    """
    Universal Crawler Service (Hunter Drones)
    Powered by Playwright for stealth, JS-execution, and dynamic interactions.
    """
    
    def __init__(self):
        self.kafka_initialized = kafka_producer_manager.initialize()
        self.browser = None
        self.playwright = None
        # Prevent concurrent initialization races (multiple scrapers booting at once)
        self._browser_lock = asyncio.Lock()

    async def _init_browser(self):
        """Initialize Playwright Engine if not running (race-safe)"""
        # Fast path: already initialized
        if self.playwright and self.browser:
            return

        async with self._browser_lock:
            # Re-check after acquiring lock
            if self.playwright and self.browser:
                return

            try:
                if not self.playwright:
                    self.playwright = await async_playwright().start()

                # Launch Chromium (headless, but with anti-bot flags)
                self.browser = await self.playwright.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-infobars',
                        '--window-size=1920,1080',
                    ],
                )
            except Exception:
                # Reset state so future attempts can retry cleanly
                try:
                    if self.browser:
                        await self.browser.close()
                except Exception:
                    pass
                try:
                    if self.playwright:
                        await self.playwright.stop()
                except Exception:
                    pass
                self.browser = None
                self.playwright = None
                raise
            
    async def create_stealth_context(self) -> BrowserContext:
        """Create a new incognito context with advanced stealth overrides"""
        await self._init_browser()
        if not self.browser:
            raise RuntimeError("Playwright browser not initialized")
        # Rotate user agents for anti-detection
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        # Randomize viewport slightly for fingerprint variance
        viewports = [
            {'width': 1920, 'height': 1080},
            {'width': 1536, 'height': 864},
            {'width': 1440, 'height': 900},
            {'width': 1366, 'height': 768},
        ]
        
        context = await self.browser.new_context(
            user_agent=random.choice(user_agents),
            viewport=random.choice(viewports),
            locale='en-US',
            timezone_id=random.choice(['America/New_York', 'America/Los_Angeles', 'Europe/London']),
            color_scheme='light',
            has_touch=False,
            is_mobile=False,
            java_script_enabled=True,
        )
        
        # Advanced stealth scripts
        await context.add_init_script("""
            // Remove webdriver flag
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            
            // Override plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Override languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            // Override visibility state
            Object.defineProperty(document, 'visibilityState', { get: () => 'visible' });
            Object.defineProperty(document, 'hidden', { get: () => false });

            // Override platform
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32'
            });
            
            // Override hardware concurrency
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8
            });
            
            // Override device memory
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8
            });
            
            // Remove automation indicators from chrome object
            if (window.chrome) {
                window.chrome.runtime = {};
            }
            
            // Override permissions query
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        return context

    async def crawl_and_stream(self, urls: List[str], intent: str = "general", mission_id: Optional[str] = None):
        """
        Deploy Hunter Drones to target URLs in parallel batches.
        """
        logger.info("Deploying Hunter Drone Squad", target_count=len(urls), intent=intent)
        
        # Process in batches to not overwhelm local resources but keep speed
        batch_size = 5
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            tasks = [self._crawl_single_target(url, intent, mission_id) for url in batch]
            await asyncio.gather(*tasks)
            # Stagger between batches
            await asyncio.sleep(random.uniform(2.0, 4.0))

    async def _crawl_single_target(self, url: str, intent: str, mission_id: Optional[str] = None):
        """Individual drone mission"""
        context = await self.create_stealth_context()
        try:
            # BLOCKED BLACKLIST: Hard stop for dead/zombie URLs
            if "chegg.com" in url or "chegg.com" in url.lower():
                logger.warning("Drone ignoring dead target (Chegg Blacklist)", url=url)
                return

            page = await context.new_page()
            # RADICAL PURGE: Block heavy tracking & social scripts to prevent networkidle hangs
            BLOCKED_DOMAINS = [
                "google-analytics.com", "googletagmanager.com", "facebook.net", 
                "clarity.ms", "hotjar.com", "linkedin.com", "doubleclick.net", 
                "quantserve.com", "scorecardresearch.com", "intercom.io"
            ]
            
            async def _handle_route(route):
                request = route.request
                url = request.url.lower()
                resource_type = request.resource_type
                
                # 1. Block heavy resource types
                if resource_type in ["image", "media", "font"]:
                    return await route.abort()
                
                # 2. Block tracking/social scripts (Exclude mission-critical APIs)
                SAFE_DOMAINS = ["api.", "graphql", "cdn-cgi", "dorahacks.io", "hackquest.io", "superteam.fun", "taikai.network"]
                if any(domain in url for domain in BLOCKED_DOMAINS):
                    # Only block if it's NOT a safe API/data domain
                    if not any(safe in url for safe in SAFE_DOMAINS):
                        return await route.abort()
                
                return await route.continue_()

            await page.route("**/*", _handle_route)

            # SET REALISTIC HEADERS
            await page.set_extra_http_headers({
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1"
            })

            logger.info("Drone approaching target", url=url)
            
            # SMART NAVIGATION
            try:
                # Use domcontentloaded for faster, less brittle navigation
                # Only use networkidle if strictly necessary (it fails on sites with constant polling)
                await page.goto(url, wait_until="domcontentloaded", timeout=90000)
            except Exception as e:
                logger.debug("Drone primary approach failed (networkidle), retrying with lenient wait", url=url)
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                except:
                    # Last resort: just wait for the request to commit
                    await page.goto(url, wait_until="commit", timeout=60000)
            
            # HUMAN INTERACTION LAYER (The "Wiggle")
            # Move mouse randomly to simulate presence
            await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # DEEP SCROLL (For Infinite Scroll sites like DoraHacks/DevPost)
            # We scroll in 3 intervals to trigger lazy loads
            for _ in range(3):
                await page.evaluate("window.scrollBy(0, 1500)")
                await asyncio.sleep(1.5)
            
            # Wait for content to stabilize
            try:
                # RADICAL: Added a 2s 'Snap Wait' for SPA hydration stabilization
                await asyncio.sleep(2.0)
                await page.wait_for_load_state("networkidle", timeout=10000)
            except:
                pass 

            # EXTRACT with retry logic for navigation errors (TAIKAI fix)
            content = None
            title = None
            for attempt in range(3):
                try:
                    content = await page.content()
                    title = await page.title()
                    break
                except Exception as nav_error:
                    if "navigating" in str(nav_error).lower():
                        logger.debug("Page still navigating, retrying...", url=url, attempt=attempt+1)
                        await asyncio.sleep(0.5 + random.random())  # 500-1500ms jitter
                        await page.wait_for_load_state("domcontentloaded", timeout=5000)
                    else:
                        raise
            
            if not content:
                logger.warning("Drone mission aborted: Failed to extract content after retries", url=url)
                return
            
            # CONTENT GUARD: Don't transmit shells or error pages
            if "Page Not Found" in title or "404" in title:
                logger.warning("Drone mission aborted: 404/Not Found", url=url, title=title)
                return
            
            # SMART CONTENT GUARD: Allow thin content for JSON API endpoints
            is_api_endpoint = '/api/' in url or '/graphql' in url
                
            if len(content) < 5000 and not is_api_endpoint:
                logger.warning("Drone mission aborted: Content too thin (Potential Loading Shell)", url=url, size=len(content))
                return
            
            await self._process_success(url, content, title, intent, mission_id)
            
        except Exception as e:
            logger.error("Drone crash", url=url, error=str(e))
        finally:
            await context.close()
            
    async def _process_success(self, url: str, html_content: str, title: str, intent: str, mission_id: Optional[str] = None):
        """Process successful extraction"""
        
        # 1. Clean / Minify HTML (basic) to save bandwidth
        # remove scripts/styles for raw storage if desired, but we keep raw for now
        
        payload = {
            "url": url,
            "title": title,
            "html": html_content[:200000],  # 200KB limit
            "crawled_at": time.time(),
            "source": self._extract_domain(url),
            "intent": intent,
            "agent_type": "HunterDrone-V1",
            "mission_id": mission_id
        }
        
        if self.kafka_initialized:
            success = kafka_producer_manager.publish_to_stream(
                topic=KafkaConfig.TOPIC_RAW_HTML,
                key=url,
                value=payload
            )
            if success:
                logger.info("Drone transmitted payload", url=url, size=len(html_content))
            else:
                logger.error("Transmission jammed (Kafka fail) - Engaging Heartbeat Fallback", url=url)
                from app.services.cortex.refinery import refinery_service
                await refinery_service.process_raw_event(key=url, value=payload) # Direct Heartbeat Injection
        else:
             logger.warning("Kafka offline - Engaging Heartbeat Fallback", url=url)
             from app.services.cortex.refinery import refinery_service
             await refinery_service.process_raw_event(key=url, value=payload) # Direct Heartbeat Injection

    def _extract_domain(self, url: str) -> str:
        from urllib.parse import urlparse
        return urlparse(url).netloc
    
    async def fetch_content(self, url: str, max_retries: int = 3) -> Optional[str]:
        """
        Direct fetch of a single URL using stealth context. 
        Returns HTML content or None on failure.
        
        Enhanced with:
        - Exponential backoff retry logic
        - Multiple wait strategies for SPAs
        - Extended timeout for slow sites (MLH, TAIKAI)
        """
        last_error = None
        
        for attempt in range(max_retries):
            context = await self.create_stealth_context()
            page = None
            try:
                page = await context.new_page()
                
                # Basic route blocking for speed (allow JSON API responses)
                async def route_handler(route):
                    if route.request.resource_type in ["image", "media", "font", "stylesheet"]:
                        await route.abort()
                    else:
                        await route.continue_()
                        
                await page.route("**/*", route_handler)
                
                logger.info("Direct fetch approaching", url=url, attempt=attempt + 1)
                
                # Try multiple loading strategies
                loaded = False
                
                # Strategy 1: domcontentloaded (fast, good for SPAs)
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    loaded = True
                except Exception as e1:
                    logger.debug("domcontentloaded failed, trying networkidle", url=url, error=str(e1)[:50])
                    
                    # Strategy 2: networkidle (slower but more complete for SPAs)
                    try:
                        await page.goto(url, wait_until="networkidle", timeout=60000)
                        loaded = True
                    except Exception as e2:
                        logger.debug("networkidle failed, trying commit", url=url, error=str(e2)[:50])
                        
                        # Strategy 3: commit (minimal, just wait for first response)
                        try:
                            await page.goto(url, wait_until="commit", timeout=30000)
                            loaded = True
                        except Exception as e3:
                            last_error = e3
                            logger.warning("All load strategies failed", url=url, attempt=attempt + 1)
                            
                if not loaded:
                    continue  # Retry with fresh context
                
                # Wait for dynamic content to render (SPAs like DoraHacks, TAIKAI)
                await asyncio.sleep(3)
                
                # Additional wait for specific slow sites
                SPA_HEAVY_SITES = ['taikai.network', 'mlh.io', 'hackquest.io', 'dorahacks.io', 'kaggle.com', 'devfolio.co']
                if any(domain in url for domain in SPA_HEAVY_SITES):
                    await asyncio.sleep(4)  # Extra 4s for heavy SPAs to fully hydrate
                    # Extra scroll to trigger lazy loading
                    try:
                        await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                        await asyncio.sleep(1.5)
                    except:
                        pass
                
                content = await page.content()
                
                # Validate content isn't empty/shell
                if len(content) > 1000:
                    return content
                else:
                    logger.warning("Content too thin, retrying", url=url, length=len(content))
                    
            except Exception as e:
                last_error = e
                logger.warning("Direct fetch attempt failed", url=url, attempt=attempt + 1, error=str(e)[:100])
            finally:
                if page: 
                    try:
                        await page.close()
                    except:
                        pass
                try:
                    await context.close()
                except:
                    pass
            
            # Exponential backoff between retries
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
        
        logger.error("Direct fetch failed after all retries", url=url, error=str(last_error) if last_error else "Unknown")
        return None

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

# Global instance
crawler_service = UniversalCrawlerService()

