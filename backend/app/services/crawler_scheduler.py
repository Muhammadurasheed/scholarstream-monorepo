
import asyncio
import structlog
from datetime import datetime
from typing import List

from app.services.crawler_service import crawler_service
from app.services.seeds import SEED_URLS

logger = structlog.get_logger()

class CrawlerScheduler:
    """
    Automated Scheduler for Universal Crawler.
    Manages the lifecycle of continuous crawling.
    """
    
    def __init__(self):
        self.running = False
        self.task = None
        
    async def start(self):
        """Start the crawling loop"""
        if self.running:
            logger.warning("Crawler Scheduler already running")
            return
            
        self.running = True
        self.task = asyncio.create_task(self._run_loop())
        logger.info("Crawler Scheduler STARTED")
        
    async def stop(self):
        """Stop the crawling loop"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Crawler Scheduler STOPPED")
        
    async def _run_loop(self):
        """Continuous crawling loop via Sentinel Agents"""
        from app.routes.crawler import sentinel_manager
        
        while self.running:
            try:
                # Check for active Sentinels
                # Patient Scheduler: Wait for Agent
                node_id = sentinel_manager.get_available_node()
                wait_retries = 0
                max_retries = 12 # 1 minute max wait
                
                while not node_id and wait_retries < max_retries:
                    logger.warning(f"No Sentinel Agents active. Waiting... ({wait_retries+1}/{max_retries})")
                    await asyncio.sleep(5)
                    node_id = sentinel_manager.get_available_node()
                    wait_retries += 1
                
                if not node_id:
                    logger.error("Scheduler Timed Out: No Agents available. Retrying next cycle.")
                    await asyncio.sleep(60)
                    continue

                logger.info("Starting distributed crawl cycle", url_count=len(SEED_URLS))
                
                for url in SEED_URLS:
                    await self._dispatch_job(url, sentinel_manager)
                    
                wait_time = 120 # 2 minutes between cycles
                logger.info(f"Cycle complete. Sleeping for {wait_time}s...")
                await asyncio.sleep(wait_time)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Crawler Scheduler crashed", error=str(e))
                await asyncio.sleep(10)

    async def _dispatch_job(self, url: str, manager, intent: str = "general"):
        """Helper to dispatch a job safely"""
        success = await manager.dispatch_crawl_job(url, intent=intent)
        if success:
             logger.info("Job dispatched to Sentinel", url=url, intent=intent)
        else:
             logger.error("Failed to dispatch job", url=url)
        await asyncio.sleep(5) # Stagger

    async def trigger_hunt(self, intent: str, location: str):
        """
        The 'Hunter Drone' Trigger.
        Spawns a highly targeted, on-demand crawl based on user intent.
        Called by Cortex when high-value user has 0 matches.
        """
        from app.routes.crawler import sentinel_manager
        logger.info(" HUNTER DRONE ACTIVATED", intent=intent, location=location)
        
        # Construct Targeted Search URLs based on intent
        # In V2, use SerpApi to find these URLs dynamically
        # For now, we map intent to known high-yield niche pools
        target_urls = []
        if "bio" in intent.lower() or "medical" in intent.lower():
            target_urls.append("https://www.grants.gov/search-grants")
        if "art" in intent.lower() or "design" in intent.lower():
            target_urls.append("https://www.arts.gov/grants")
        
        # If no specific mapping, hit the big aggregators with query params (Mocked)
        if not target_urls:
            target_urls.append(f"https://www.google.com/search?q={intent}+scholarships+{location}")

        # Priority Dispatch
        for url in target_urls:
             # Fire and forget - don't block the API response
             asyncio.create_task(self._dispatch_job(url, sentinel_manager, intent=f"hunt:{intent}"))

# Global Scheduler Instance
crawler_scheduler = CrawlerScheduler()
