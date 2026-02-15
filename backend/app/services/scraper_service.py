"""
Opportunity Discovery Service - CORTEX PIPELINE ONLY

All discovery is handled by the Playwright-based Cortex pipeline:
1. Sentinel patrols target URLs with Playwright stealth
2. Raw HTML streams to Kafka
3. Gemini AI extracts structured opportunities
4. Enriched data pushed via WebSocket

Legacy httpx scrapers have been REMOVED - they get blocked by anti-bot systems.
"""
from typing import List, Dict, Any
import structlog

logger = structlog.get_logger()


class OpportunityScraperService:
    """
    Discovery service - delegates to Cortex pipeline.
    
    Legacy httpx-based scraping has been removed.
    Use /api/crawler/patrol to trigger real discovery.
    """
    
    def __init__(self):
        logger.info(
            "OpportunityScraperService: CORTEX MODE ACTIVE",
            message="All discovery via Playwright-based Sentinel patrols",
            legacy_scrapers="REMOVED"
        )

    async def discover_all_opportunities(self, user_profile: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        DEPRECATED: Legacy scraping is disabled.
        
        Use the Cortex pipeline instead:
        - POST /api/crawler/patrol → triggers Sentinel with Playwright
        - WebSocket → receives enriched opportunities in real-time
        
        Returns empty list - real data comes from Cortex pipeline.
        """
        logger.warning(
            "discover_all_opportunities() called but legacy scrapers are REMOVED",
            recommendation="Use /api/crawler/patrol to trigger Cortex pipeline"
        )
        
        return []
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get status of the Cortex discovery pipeline"""
        return {
            'mode': 'CORTEX_PLAYWRIGHT_ONLY',
            'legacy_scrapers': 0,
            'message': 'All discovery handled by Playwright Sentinel patrols',
            'pipeline': [
                'Sentinel (navigator.py) → Target URLs',
                'UniversalCrawlerService (crawler_service.py) → Playwright stealth',
                'Kafka → Raw HTML streaming',
                'Refinery (refinery.py) → Gemini AI extraction',
                'Enriched opportunities → Frontend WebSocket'
            ]
        }
    
    async def close(self):
        """No resources to close - Playwright managed by crawler_service"""
        pass


# Global scraper service instance
scraper_service = OpportunityScraperService()
