
import asyncio
import structlog
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.services.crawler_service import crawler_service
from app.services.kafka_config import KafkaConfig, kafka_producer_manager
from app.services.discovery_pulse import discovery_pulse
import random
import string

logger = structlog.get_logger()

class Sentinel:
    """
    Proactive Background Worker (Cortex V2).
    Delegates mission execution to Hunter Drones (UniversalCrawlerService).
    """
    
    """
    COMPREHENSIVE TARGET LIST V2 - All opportunity sources
    These URLs are crawled with Playwright stealth to bypass anti-bot
    EXPANDED: Added more hackathon platforms, bounties, and grants
    """
    TARGETS = [
        # ======== HACKATHONS (Global) ========
        "https://devpost.com/hackathons",
        "https://mlh.io/seasons/2026/events",
        "https://angelhack.com/events/",
        "https://www.hackquest.io/hackathons",
        "https://devfolio.co/hackathons",
        "https://hackerearth.com/challenges/",
        "https://lablab.ai/event",  # AI Hackathons
        "https://unstop.com/hackathons",  # Indian ecosystem but global
        "https://hackathon.io/events",  # Hackathon aggregator
        "https://taikai.network/hackathons",
        "https://www.bemyapp.com/events/",
        "https://eventornado.com/",
        "https://gitcoin.co/hackathons",
        
        # ======== BOUNTIES & BUG BOUNTIES ========
        "https://immunefi.com/explore",
        "https://gitcoin.co/grants-stack/explorer",
        "https://hackerone.com/bug-bounty-programs",
        "https://bugcrowd.com/programs",
        "https://intigriti.com/researchers/bug-bounty-programs",
        "https://bountycaster.xyz/",  # Web3 bounties
        "https://earn.superteam.fun/bounties/",  # Solana ecosystem
        "https://replit.com/bounties",
        "https://www.algorand.foundation/bounties",
        "https://dorahacks.io/bounty", # DoraHacks Bounties
        "https://dorahacks.io/grant",  # DoraHacks Grants
        
        # ======== WEB3 GRANTS & ECOSYSTEMS ========
        "https://questbook.xyz/",
        "https://grants.gitcoin.co/",
        "https://aave.com/grants/",
        "https://compound.finance/grants",
        "https://ethereum.org/en/community/grants/",
        "https://solana.com/grants",
        "https://near.org/grants/",
        "https://stacks.org/grants",
        
        # ======== COMPETITIONS ========
        "https://www.kaggle.com/competitions",
        "https://codeforces.com/contests",
        "https://topcoder.com/challenges",
        "https://www.codechef.com/contests",
        "https://atcoder.jp/contests",
        "https://leetcode.com/contest/",
        
        # ======== SCHOLARSHIPS (Global Focus) ========
        "https://bold.org/scholarships/",
        "https://www.scholarships.com/financial-aid/college-scholarships/scholarship-directory",
        "https://www.fastweb.com/college-scholarships",
        "https://www.niche.com/colleges/scholarships/",
        "https://www.unigo.com/scholarships/all",
        "https://www.goingmerry.com/scholarships",
        "https://www.scholarshipamerica.org/browse-scholarships/",
        "https://www.internationalscholarships.com/",
        
        # ======== INTERNSHIPS (Tech Hubs) ========
        "https://www.internships.com/search/posts?keywords=software%20engineering",
        "https://www.levels.fyi/internships/",
        "https://wellfound.com/role/l/internship/software-engineer",
    ]

    async def patrol(self):
        """Deploy Hunter Drones to patrol targets"""
        mission_id = "patrol_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
        logger.info("Sentinel deploying Hunter Drones", target_count=len(self.TARGETS), mission_id=mission_id)
        
        discovery_pulse.announce_mission(mission_id, "Target Selection", "active")
        
        try:
            # Delegate to the robust Universal Crawler (Playwright)
            await crawler_service.crawl_and_stream(self.TARGETS, intent="patrol", mission_id=mission_id)
            discovery_pulse.complete_mission(mission_id, found_count=len(self.TARGETS))
        except Exception as e:
            logger.error("Sentinel patrol mission failed", error=str(e))
            discovery_pulse.complete_mission(mission_id, found_count=0)

    async def heavy_hunt(self, platforms: Optional[List[str]] = None):
        """
        Execute a high-intensity hunt for specific high-value platforms.
        Used to satisfy 'Mass Opportunity' requests.
        """
        PLATFORM_MAP = {
            "hackerone": "https://hackerone.com/bug-bounty-programs",
            "hackquest": "https://www.hackquest.io/hackathons",
            "replit": "https://replit.com/bounties",
            "algorand": "https://www.algorand.foundation/bounties",
            "superteam": ["https://earn.superteam.fun/bounties/", "https://earn.superteam.fun/grants/"],
            "intigriti": "https://www.intigriti.com/researchers/bug-bounty-programs",
            "taikai": "https://taikai.network/hackathons"
        }
        
        targets = []
        if platforms:
            for p in platforms:
                p_lower = p.lower()
                if p_lower in PLATFORM_MAP:
                    url = PLATFORM_MAP[p_lower]
                    if isinstance(url, list): targets.extend(url)
                    else: targets.append(url)
        else:
            # Hunt all high-value hubs if no platforms specified
            for urls in PLATFORM_MAP.values():
                if isinstance(urls, list): targets.extend(urls)
                else: targets.append(urls)
                
        logger.info("Sentinel initiating HEAVY HUNT", targets=targets)
        try:
            # Run with high priority intent
            await crawler_service.crawl_and_stream(targets, intent="heavy_hunt")
        except Exception as e:
            logger.error("Heavy hunt mission failed", error=str(e))

class Scout:
    """
    Reactive On-Demand Worker.
    Triggered by Chat requests to perform targeted searches via Hunter Drones.
    """
    
    async def execute_mission(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute a targeted search mission.
        """
        mission_id = "scout_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
        logger.info("Scout dispatching drone squad", mission=query, mission_id=mission_id)
        
        discovery_pulse.announce_mission(mission_id, f"Searching: {query}", "active")
        
        # 1. Generate Search URL (DuckDuckGo or Google)
        search_urls = [
            f"https://duckduckgo.com/?q={query.replace(' ', '+')}",
            f"https://www.google.com/search?q={query.replace(' ', '+')}"
        ]
        
        # 2. Dispatch Drones
        # Note: crawl_and_stream handles browser context and stealth
        try:
            await crawler_service.crawl_and_stream(search_urls, intent="scout_search", mission_id=mission_id)
            return [{"url": u, "status": "dispatched"} for u in search_urls]
        except Exception as e:
            logger.error("Scout mission failed", error=str(e))
            return []

# Global Instances
sentinel = Sentinel()
scout = Scout()
