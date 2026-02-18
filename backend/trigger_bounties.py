
import asyncio
import structlog
import os
import sys

# Ensure backend is in path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.services.cortex.navigator import sentinel
from app.services.crawler_service import crawler_service
from app.services.kafka_config import kafka_producer_manager
from app.services.cortex.refinery import refinery_service

logger = structlog.get_logger()

async def trigger_bounty_hunt():
    """
    Explicitly trigger the bounty hunting targets
    """
    print("Triggering Bounty Hunt Protocol...")
    
    # Bounty specific targets
    bounty_targets = [
        "https://immunefi.com/explore",
        "https://bugcrowd.com/programs",
        "https://hackerone.com/bug-bounty-programs",
        "https://gitcoin.co/grants-stack/explorer"
    ]
    
    # Initialize Kafka (attempt)
    conn = kafka_producer_manager.initialize()
    print(f"Connection Status: {conn}")

    # Directly invoke crawler service
    try:
        # We use a short list to test immediate results
        await crawler_service.crawl_and_stream(bounty_targets, intent="bounty_hunt_test")
        print("Bounty Hunt Dispatch Complete")
    except Exception as e:
        print(f"Bounty Hunt Failed: {e}")

if __name__ == "__main__":
    asyncio.run(trigger_bounty_hunt())
