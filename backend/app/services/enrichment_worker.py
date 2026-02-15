
import asyncio
import json
import time
from typing import List, Dict, Any
from confluent_kafka import Consumer, KafkaError, Message
import structlog

from app.config import settings
from app.services.kafka_config import KafkaConfig, kafka_producer_manager
from app.services.ai_enrichment_service import ai_enrichment_service
from app.services.discovery_pulse import discovery_pulse

logger = structlog.get_logger()

class EnrichmentWorker:
    """
    AI REQUEST CONSUMER (The "Refinery")
    Consumes RAW HTML from 'raw-html-stream'.
    Extracts structured opportunities using Gemini.
    Publishes to 'enriched-opportunities-stream'.
    """
    
    def __init__(self):
        self.config = KafkaConfig()
        self.consumer_config = self.config.get_consumer_config(group_id="ai-refinery-v1")
        self.running = False
        
    async def start(self):
        """Start the AI processing loop"""
        if not self.consumer_config:
            logger.error("Kafka configuration missing, cannot start worker")
            return
            
        logger.info("Starting AI Refinery Worker...")
        
        # Initialize producer
        if not kafka_producer_manager.initialize():
            logger.error("Failed to initialize producer")
            return
            
        # Initialize consumer
        consumer = Consumer(self.consumer_config)
        consumer.subscribe([KafkaConfig.TOPIC_RAW_HTML])
        
        self.running = True
        logger.info(f"Subscribed to {KafkaConfig.TOPIC_RAW_HTML}")
        logger.info("AI Refinery: READY. Waiting for HTML...")
        
        try:
            while self.running:
                # BATCH COLLECTION: Standardized to 1 for Maximum Reliability
                batch_messages = []
                start_collect = time.time()
                
                # Consume single message (Serial mode for absolute yield)
                # We use asyncio.to_thread for Kafka polling
                msg = await asyncio.to_thread(consumer.poll, 1.0)
                
                if msg is None:
                    await asyncio.sleep(0.1)
                    continue
                    
                if msg.error():
                    if msg.error().code() != KafkaError._PARTITION_EOF:
                        logger.error(f"Consumer error: {msg.error()}")
                    continue
                    
                try:
                    payload = json.loads(msg.value().decode('utf-8'))
                    # Check for pre-extracted data first
                    if payload.get("extracted_data"):
                        batch_messages.append(payload)
                    elif payload.get("html") and payload.get("url"):
                        batch_messages.append(payload)
                except Exception as e:
                    logger.error("Failed to decode message", error=str(e))

                if not batch_messages:
                    continue
                
                # HARD DEAD-LETTER FILTER: Drop any Chegg messages from the queue
                # This clears old Kafka logs without spamming warnings
                if any("chegg.com" in (m.get("url") or "") for m in batch_messages):
                    logger.debug("Queue Flush: Dropped dead Chegg message")
                    continue

                # PROCESS PAYLOAD
                start_time = time.time()
                opportunities = []
                
                # Extract identifiers from the batch
                urls = [m.get("url") for m in batch_messages if m.get("url")]
                mission_id = batch_messages[0].get("mission_id") if batch_messages else None
                
                # Check for pre-extracted data in batch
                pre_extracted = [m.get("extracted_data") for m in batch_messages if m.get("extracted_data")]
                
                if pre_extracted:
                    logger.info("Using pre-extracted data (Deep Scraper Bypass)", count=len(pre_extracted))
                    opportunities = pre_extracted
                else:
                    # Extract using AI Enrichment Service
                    opportunities = await ai_enrichment_service.extract_opportunities_from_html_batch(batch_messages)
                
                duration = time.time() - start_time
                
                if not opportunities:
                    logger.warning(f"No opportunities extracted from target", duration=f"{duration:.2f}s", url=urls[0] if urls else "unknown")
                    if mission_id:
                        discovery_pulse.complete_mission(mission_id, found_count=0)
                    continue
                    
                logger.info(f"Discovery Yield: {len(opportunities)} items", duration=f"{duration:.2f}s", url=urls[0] if urls else "unknown", source="pre-extracted" if pre_extracted else "ai")
                if mission_id:
                    discovery_pulse.complete_mission(mission_id, found_count=len(opportunities))

                # PUBLISH RESULTS
                for opp in opportunities:
                    enriched_message = {
                        'source': "multi-batch", 
                        'enriched_data': opp,
                        'raw_data': {}, 
                        'enriched_at': time.time(),
                        'ai_model': settings.gemini_model,
                        'origin_url': opp.get('url') or (urls[0] if urls else None)
                    }
                    
                    kafka_producer_manager.publish_to_stream(
                        topic=KafkaConfig.TOPIC_OPPORTUNITY_ENRICHED,
                        key="ai-refinery",
                        value=enriched_message
                    )
                
                kafka_producer_manager.flush()
                        
        except Exception as e:
            logger.error("Worker lifecycle crashed", error=str(e))
                    
        except KeyboardInterrupt:
            logger.info("Stopping worker...")
        finally:
            self.close()

    def stop(self):
        """Stop the worker gracefully"""
        self.running = False

    def close(self):
        """Close resources"""
        if self.running: 
             logger.info("Closing AI Refinery Worker")
        kafka_producer_manager.close()

# Global instance
enrichment_worker = EnrichmentWorker()

if __name__ == "__main__":
    asyncio.run(enrichment_worker.start())
