"""
Background Jobs - Automated Opportunity Discovery
Scheduled jobs that refresh opportunity cache every 6 hours
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import structlog

from app.services.scraper_service import scraper_service
from app.services.ai_service import ai_service
from app.services.opportunity_converter import convert_to_scholarship
from app.database import db
from app.models import UserProfile

logger = structlog.get_logger()

# Global scheduler instance
scheduler = AsyncIOScheduler()


async def refresh_opportunities_job():
    """
    Scheduled job to refresh opportunities cache
    Runs every 6 hours to keep database fresh
    """
    logger.info("Starting scheduled opportunity refresh")
    
    try:
        # 1. Scrape all sources
        raw_opportunities = await scraper_service.discover_all_opportunities({})
        logger.info(f"Scraped {len(raw_opportunities)} raw opportunities")
        
        # 2. Enrich with AI (batched to save API calls)
        from app.services.ai_enrichment_service import ai_enrichment_service
        enriched = await ai_enrichment_service.enrich_opportunities_batch(raw_opportunities)
        logger.info(f"Enriched {len(enriched)} opportunities")
        
        # 3. Convert to Scholarship model
        # Create a generic user profile for conversion
        generic_profile = UserProfile(
            name="System",
            academic_status="undergraduate",
            major="Computer Science",
            gpa=3.5,
            graduation_year="2026",
            interests=["Technology"],
            background=[]
        )
        
        converted_opportunities = []
        for opp_data in enriched:
            try:
                scholarship = convert_to_scholarship(opp_data, generic_profile)
                if scholarship:
                    converted_opportunities.append(scholarship)
            except Exception as e:
                logger.error("Failed to convert opportunity", error=str(e))
                continue
        
        # 4. Cache in Firebase
        for opp in converted_opportunities:
            try:
                await db.save_scholarship(opp)
            except Exception as e:
                logger.error("Failed to cache opportunity", scholarship_id=opp.id, error=str(e))
        
        logger.info(
            "Opportunity refresh complete",
            total_scraped=len(raw_opportunities),
            total_cached=len(converted_opportunities)
        )
        
    except Exception as e:
        logger.error("Scheduled refresh failed", error=str(e), exc_info=True)


def start_scheduler():
    """
    Initialize and start the background job scheduler
    """
    logger.info("Initializing background job scheduler")
    
    # Schedule opportunity refresh every 6 hours
    scheduler.add_job(
        refresh_opportunities_job,
        'interval',
        hours=6,
        id='refresh_opportunities',
        replace_existing=True,
        max_instances=1
    )
    
    # Run once on startup (after 30 seconds to allow app initialization)
    scheduler.add_job(
        refresh_opportunities_job,
        'date',
        run_date=datetime.now() + timedelta(seconds=30),
        id='initial_refresh',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Background job scheduler started")


def stop_scheduler():
    """
    Stop the background job scheduler
    """
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Background job scheduler stopped")
