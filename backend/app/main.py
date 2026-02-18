"""
ScholarStream FastAPI Backend
Main application entry point
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import structlog
import logging
import asyncio

from app.config import settings
from app.routes import scholarships, applications, chat, websocket, extension, documents

# Configure structured logging with readable format for development
log_renderer = (
    structlog.processors.JSONRenderer() 
    if settings.environment == "production" 
    else structlog.dev.ConsoleRenderer(colors=True)
)

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S" if settings.environment != "production" else "iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        log_renderer
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="ScholarStream API",
    description="AI-powered scholarship discovery and matching platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
allow_origins = settings.cors_origins_list + [
    "http://localhost:8000",
    "http://localhost:8081",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8081",
    "chrome-extension://"  # Allow Chrome extensions
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev, wildcard is safest for extension weirdness
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    logger.info(
        "Request received",
        method=request.method,
        path=request.url.path,
        client=request.client.host if request.client else None
    )
    
    response = await call_next(request)
    
    logger.info(
        "Request completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code
    )
    
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        path=request.url.path,
        method=request.method,
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred"
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": "1.0.0"
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "ScholarStream API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# Include routers
app.include_router(scholarships.router)
app.include_router(applications.router)
app.include_router(chat.router)
app.include_router(websocket.router)
app.include_router(extension.router)
app.include_router(documents.router)
from app.routes import crawler
app.include_router(crawler.router)


# Initialize Event Broker (Global)
from app.infrastructure.memory_broker import MemoryBroker
# In a real app, we'd use a factory based on settings.event_broker_type
broker = MemoryBroker()

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info(
        "Starting ScholarStream API",
        environment=settings.environment,
        debug=settings.debug
    )
    
    # 1. Start Event Broker
    await broker.start()
    
    # 2. Wire up Event Subscribers (The Wiring)
    # Refinery: Listens for Raw HTML -> Enriches
    from app.services.cortex.refinery import refinery_service
    await broker.subscribe(settings.topic_raw_html, refinery_service.handle_raw_html_event)
    
    # WebSocket: Listens for Enriched Data -> Pushes to UI
    from app.routes.websocket import subscribe_to_opportunities
    await subscribe_to_opportunities()
    
    logger.info("Event Mesh sub-systems wired successfully")

    # === DEVPOST API SCRAPER: IMMEDIATE DATABASE POPULATION ===
    # Run DevPost API scraper on startup to immediately populate database
    # This is fast (API-based) and doesn't require Playwright
    async def run_devpost_api_scraper():
        await asyncio.sleep(5)  # Wait 5 seconds for server to settle
        try:
            from app.services.scrapers.hackathons.devpost_api_scraper import populate_database_with_devpost
            logger.info("Starting DevPost API scraper for immediate database population...")
            saved = await populate_database_with_devpost()
            logger.info(f"DevPost API scraper complete: {saved} hackathons saved to database")
        except Exception as e:
            logger.warning("DevPost API scraper failed, Sentinel will handle later", error=str(e))

    asyncio.create_task(run_devpost_api_scraper())

    # === MULTI-PLATFORM SCRAPER: DoraHacks, Immunefi, Superteam, Gitcoin, MLH ===
    # Run after DevPost to get bounties, more hackathons, and MLH events
    async def run_multi_platform_scraper():
        await asyncio.sleep(15)  # Wait 15 seconds (after DevPost scraper)
        try:
            # MLH Events Scraper
            try:
                from app.services.scrapers.hackathons.mlh_scraper import populate_database_with_mlh
                logger.info("Starting MLH scraper...")
                mlh_count = await populate_database_with_mlh()
                logger.info(f"MLH scraper complete: {mlh_count} events saved")
            except Exception as e:
                logger.warning("MLH scraper failed", error=str(e))
                
            # TAIKAI Scraper
            try:
                from app.services.scrapers.hackathons.taikai_scraper import populate_database_with_taikai
                logger.info("Starting TAIKAI scraper...")
                taikai_count = await populate_database_with_taikai()
                logger.info(f"TAIKAI scraper complete: {taikai_count} events saved")
            except Exception as e:
                logger.warning("TAIKAI scraper failed", error=str(e))

            # HackQuest Scraper
            try:
                from app.services.scrapers.hackathons.hackquest_scraper import populate_database_with_hackquest
                logger.info("Starting HackQuest scraper...")
                hq_count = await populate_database_with_hackquest()
                logger.info(f"HackQuest scraper complete: {hq_count} events saved")
            except Exception as e:
                logger.warning("HackQuest scraper failed", error=str(e))
                
            # Intigriti Scraper
            try:
                from app.services.scrapers.bounties.intigriti_scraper import populate_database_with_intigriti
                logger.info("Starting Intigriti scraper...")
                int_count = await populate_database_with_intigriti()
                logger.info(f"Intigriti scraper complete: {int_count} bounties saved")
            except Exception as e:
                logger.warning("Intigriti scraper failed", error=str(e))
            
            # Multi-platform bounties (DoraHacks, Superteam, Gitcoin, Immunefi)
            from app.services.scrapers.bounties.multi_platform_scraper import populate_database_multi_platform
            logger.info("Starting multi-platform scraper (DoraHacks, Immunefi, Superteam, Gitcoin)...")
            results = await populate_database_multi_platform()
            logger.info(f"Multi-platform scraper complete", **results)
        except Exception as e:
            logger.warning("Multi-platform scraper failed", error=str(e))

    asyncio.create_task(run_multi_platform_scraper())

    # === CORTEX: AUTO-START SENTINEL PATROLS ===
    # The Sentinel will run on a schedule, patrolling opportunity hubs.
    # Default: Every 6 hours. Delayed start to not block server.
    async def run_sentinel_scheduler():
        # Delay first patrol to allow server to fully start
        await asyncio.sleep(10)  # Wait 10 seconds before first patrol
        
        while True:
            try:
                from app.services.cortex.navigator import sentinel
                logger.info("Sentinel starting periodic patrol mission (30m interval)...")
                await sentinel.patrol()
                logger.info("Sentinel patrol mission complete. Sleeping for 30 minutes.")
            except Exception as e:
                logger.error("Sentinel patrol loop error", error=str(e))
            
            await asyncio.sleep(1800)  # 30 minutes (Live Hunting Mode)

    asyncio.create_task(run_sentinel_scheduler())
    logger.info("Sentinel Patrol Loop scheduled (30-minute Live Hunting intervals)")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down ScholarStream API")
    
    # Stop Event Broker
    await broker.stop()
    
    # Close scraper HTTP client
    from app.services.scraper_service import scraper_service
    await scraper_service.close()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
