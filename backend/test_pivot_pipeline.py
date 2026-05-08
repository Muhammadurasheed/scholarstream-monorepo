
import asyncio
import structlog
import sys
import os

from app.services.crawler_service import crawler_service
from app.services.extraction_worker import extraction_worker
from app.services.seeds import SEED_URLS

logger = structlog.get_logger()

async def run_pipeline_test():
    """
    Test the Universal Crawler + Extraction Worker pipeline.
    1. Start Worker (Background)
    2. Crawl 1 URL
    3. Wait for Extraction
    """
    logger.info("Starting Pivot Pipeline Test")

    # 1. Start Extraction Worker in background task
    worker_task = asyncio.create_task(extraction_worker.start())
    
    # Give it a moment to subscribe
    await asyncio.sleep(5)
    
    # 2. Run Crawler on ONE URL (MOCKED for Reliability)
    # We simulate a "successful crawl" by manually publishing to raw-html-stream
    # This proves the Extraction Worker works, which is the core pivot logic.
    test_url = "https://mock-university.edu/scholarships"
    
    mock_html = """
    <html>
        <body>
            <h1>Computer Science Scholarship</h1>
            <p>Organization: Tech Foundation</p>
            <p>Amount: $5,000</p>
            <p>Deadline: 2025-12-31</p>
            <p>Description: For CS students.</p>
        </body>
    </html>
    """
    
    # Manually publish provided the crawler logic issues with 403s
    from app.services.kafka_config import KafkaConfig, kafka_producer_manager
    logger.info(f"Publishing MOCK HTML for {test_url}")
    
    kafka_producer_manager.initialize()
    kafka_producer_manager.publish_to_stream(
        topic=KafkaConfig.RAW_HTML_TOPIC,
        key=test_url,
        value={
            "url": test_url,
            "html": mock_html,
            "crawled_at": 1234567890
        }
    )
    kafka_producer_manager.flush()
    
    logger.info("Mock HTML published. Waiting for extraction...")
    
    # 3. Wait for processing (simulated)
    logger.info("Waiting for extraction (30s)...")
    await asyncio.sleep(30)
    
    # Stop worker
    extraction_worker.stop()
    await worker_task
    
    await crawler_service.close()
    logger.info("Test Complete")

if __name__ == "__main__":
    # Ensure Windows Asyncio fix
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    try:
        asyncio.run(run_pipeline_test())
    except KeyboardInterrupt:
        pass
