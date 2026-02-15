
import structlog
import json
from datetime import datetime
from typing import Optional, List
from app.services.kafka_config import KafkaConfig, kafka_producer_manager
from app.services.cortex.reader_llm import reader_llm
from app.models import OpportunitySchema
from app.config import settings
from app.database import db

logger = structlog.get_logger()

class RefineryService:
    """
    The Refinery: Turns Raw Data into Verified Intelligence.
    Consumes: cortex.raw.html.v1
    Produces: opportunity.enriched.v1
    """

    async def process_raw_event(self, key: str, value: dict):
        """
        Process a single raw event from the stream.
        V2: Uses parse_multiple for batch extraction from list pages.
        """
        url = value.get("url")
        raw_html = value.get("html")
        source = value.get("source")
        
        logger.info("Refinery V2: Processing Raw Event", url=url, source=source)
        
        # 1. Extract Data (Use Reader LLM V2 - Multi-extraction)
        if not raw_html:
            logger.warning("Empty HTML in raw event", url=url)
            return

        # V2: Extract MULTIPLE opportunities from list pages
        opportunities: List[OpportunitySchema] = await reader_llm.parse_multiple(raw_html, url, max_items=50)
        
        if not opportunities:
            logger.warning("No opportunities extracted", url=url)
            return
        
        logger.info(f"Extracted {len(opportunities)} opportunities from {url[:50]}")
        
        # 2. Process each opportunity
        processed_count = 0
        for opportunity in opportunities:
            try:
                # 2.1 Strict Expiration Gate
                if self._is_expired(opportunity.deadline_timestamp):
                    logger.debug("Dropped Expired", title=opportunity.title[:30] if opportunity.title else "N/A")
                    continue

                # 2.2 Geo-Tagging
                opportunity.geo_tags = self._enrich_geo_tags(opportunity)
                
                # 2.3 Type-Tagging
                opportunity.type_tags = self._enrich_type_tags(opportunity)
                
                # 2.4 Skip Vectorization for speed (can be done async later)
                # from app.services.vectorization_service import vectorization_service
                # opportunity.embedding = await vectorization_service.vectorize_opportunity(opportunity)

                # 3. Publish to Verified Stream
                await self._publish_verified(opportunity)
                processed_count += 1
                
            except Exception as e:
                logger.error("Failed to process opportunity", error=str(e))
                continue
        
        logger.info(f"Refinery Complete: {processed_count}/{len(opportunities)} opportunities processed from {url[:40]}")

    def _is_expired(self, deadline_ts: int) -> bool:
        """Strict Expiration Logic"""
        if not deadline_ts: return False # Keep if unknown, flag later
        now_ts = int(datetime.now().timestamp())
        return deadline_ts < now_ts

    def _enrich_geo_tags(self, opp: OpportunitySchema) -> List[str]:
        """Auto-detect Global vs Local"""
        tags = set(opp.geo_tags)
        text = (opp.description + " " + str(opp.eligibility_text)).lower()
        
        # Global Indicators
        if any(w in text for w in ["remote", "online", "global", "international", "worldwide"]):
            tags.add("Global")
            
        # Regional Indicators (Example: Nigeria)
        if any(w in text for w in ["nigeria", "lagos", "abuja", "africa"]):
            tags.add("Nigeria")
            
        # Defaults
        if not tags:
            tags.add("Global") # Default to Global if unsure
            
        return list(tags)

    def _enrich_type_tags(self, opp: OpportunitySchema) -> List[str]:
        tags = set(opp.type_tags)
        text = (opp.title + " " + opp.description).lower()
        
        if "hackathon" in text: tags.add("Hackathon")
        if "grant" in text: tags.add("Grant")
        if "scholarship" in text: tags.add("Scholarship")
        if "bounty" in text: tags.add("Bounty")
        
        return list(tags)

    async def _publish_verified(self, opp: OpportunitySchema):
        # Fallback Strategy: If Kafka is down, save directly to DB (The Heartbeat)
        success = kafka_producer_manager.publish_to_stream(
            topic=KafkaConfig.TOPIC_OPPORTUNITY_ENRICHED,
            key=opp.id, # Hash ID
            value=opp.model_dump() # Use model_dump() for Pydantic v2 consistency
        )
        
        if success:
            logger.info("Verified Opportunity Published to Stream", title=opp.title, tags=opp.geo_tags)
        else:
            logger.warning("Kafka Stream Failed - Engaging Heartbeat Fallback", title=opp.title)
            await self._persist_fallback(opp)

    async def _persist_fallback(self, opp: OpportunitySchema):
        """Direct-to-Database Fallback (When Kafka is broken)"""
        try:
            await db.save_scholarship(opp)
            logger.info("Heartbeat Fallback: Saved to DB directly", title=opp.title)
        except Exception as e:
            logger.error("Heartbeat Fallback Failed", error=str(e))

refinery_service = RefineryService()
