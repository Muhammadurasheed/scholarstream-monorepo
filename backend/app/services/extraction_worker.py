
import asyncio
import json
import structlog
from typing import Dict, Any, List
from confluent_kafka import Consumer, KafkaException

from app.services.kafka_config import KafkaConfig, kafka_producer_manager
from app.services.ai_enrichment_service import ai_enrichment_service

logger = structlog.get_logger()

class ExtractionWorker:
    """
    Consumes raw HTML from Kafka, uses Gemini to extract opportunities,
    and publishes structured JSON to the opportunities stream.
    """

    def __init__(self):
        self.config = KafkaConfig()
        self.consumer_config = self.config.get_consumer_config(group_id='html-extractor-group-v1')
        self.running = False
        
    async def start(self):
        """Start the extraction worker loop"""
        if not self.config.enabled:
            logger.warning("Kafka disabled, extraction worker not starting")
            return

        self.running = True
        consumer = Consumer(self.consumer_config)
        
        try:
            consumer.subscribe([KafkaConfig.RAW_HTML_TOPIC])
            logger.info(f"Extraction Worker subscribed to {KafkaConfig.RAW_HTML_TOPIC}")

            while self.running:
                # Poll for messages
                msg = await asyncio.to_thread(consumer.poll, 1.0)
                
                if msg is None:
                    continue
                    
                if msg.error():
                    logger.error(f"Consumer error: {msg.error()}")
                    continue

                try:
                    # Parse message
                    payload = json.loads(msg.value().decode('utf-8'))
                    url = payload.get('url')
                    html = payload.get('html')
                    
                    if not url or not html:
                        logger.warning("Invalid message payload", payload_keys=payload.keys())
                        continue

                    logger.info(f"Processing HTML from {url}", size=len(html))

                    # 1. Extract Opportunities using Gemini
                    extracted_opps = await ai_enrichment_service.extract_opportunities_from_html(html, url)
                    
                    if not extracted_opps:
                        logger.warning(f"No opportunities extracted from {url}")
                        continue
                        
                    logger.info(f"Extracted {len(extracted_opps)} opportunities from {url}")

                    # 2. Publish to Raw Opportunities Stream
                    # We publish each opportunity individually or as a batch?
                    # The EnrichmentWorker expects individual messages usually, or does it?
                    # Let's check. My EnrichmentWorker consumes raw-opportunities-stream.
                    # Usually consumers handle one message at a time.
                    # However, to be efficient, let's publish individually so they can be load balanced.
                    
                    kafka_producer_manager.initialize() # Ensure initialized
                    
                    for opp in extracted_opps:
                        # Add metadata
                        opp['params'] = {
                            'source_url': url,
                            'extracted_at': payload.get('crawled_at')
                        }
                        
                        kafka_producer_manager.publish_to_stream(
                            topic=KafkaConfig.RAW_OPPORTUNITIES_TOPIC,
                            key=opp.get('url', url), # Use opp URL as key for partitioning
                            value=opp
                        )
                        
                    kafka_producer_manager.flush()
                    logger.info(f"Published {len(extracted_opps)} opportunities to stream")

                except Exception as e:
                    logger.error("Error processing message", error=str(e))
        
        except Exception as e:
            logger.critical("Extraction Worker failed", error=str(e))
        finally:
            consumer.close()
            logger.info("Extraction Worker stopped")

    def stop(self):
        self.running = False

# Global instance
extraction_worker = ExtractionWorker()
