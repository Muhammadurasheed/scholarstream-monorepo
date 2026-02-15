
import asyncio
import structlog
import json
from app.services.kafka_config import KafkaConfig, kafka_producer_manager
from app.services.matching_engine import matching_engine
from app.database import db
from app.models import Scholarship, DeepUserProfile

logger = structlog.get_logger()

class MatchingWorker:
    """
    Consumes: opportunity.enriched.v1
    Action: Matches opportunities against Active Users
    Produces: user.notifications.v1 (via WebSocket logic)
    """
    
    async def start(self):
        logger.info("Matching Worker Started")
        # In a real app, this would use a proper Kafka Consumer loop (aiokafka)
        # For this implementation, we assume a function is called or we simulate the loop
        # We will expose a method 'process_enriched_opportunity' that the generic consumer calls
    
    async def process_enriched_opportunity(self, key: str, value: dict):
        """
        Process a single Enriched Opportunity.
        Find users who match this opportunity.
        """
        try:
            # 1. Parse Opportunity
            opp = Scholarship(**value)
            logger.info("Matching Worker processing", opp_id=opp.id, title=opp.title)
            
            # 2. Fetch Active Users (Simulated: In prod, iterate through users or use vector search on USER index)
            # For FAANG-scale, we'd use a Vector DB (Pinecone/Milvus) to find users CLOSE to this opportunity vector.
            # Here, we'll fetch all users (assuming low scale for MVP) or a set of active users.
            users = await db.get_all_users() # Assuming this exists and returns list of UserProfile/DeepUserProfile
            
            matched_count = 0
            
            for user in users:
                # Convert to DeepUserProfile if needed 
                deep_profile = self._ensure_deep_profile(user)
                
                # 3. Calculate Score
                score = await matching_engine.calculate_match_score(opp, deep_profile)
                
                # 4. Filter & Notify
                if score >= 50: # Threshold
                    opp.match_score = score
                    await db.save_user_match(user.id, opp)
                    
                    # Notify via WebSocket (Conceptually pushing to a user topic)
                    # The WebSocket service listens to user-specific channels
                    # We can publish to 'user.matches' topic which WebSocket service consumes
                    self._notify_user(user.id, opp)
                    matched_count += 1
            
            logger.info("Matching Complete", opp_id=opp.id, matched_users=matched_count)

        except Exception as e:
            logger.error("Matching Worker failed", error=str(e), key=key)

    def _ensure_deep_profile(self, user_data) -> DeepUserProfile:
        """Helper to cast DB user to DeepUserProfile"""
        # Logic to fill missing deep fields if necessary
        # This is a stub for now
        if isinstance(user_data, DeepUserProfile):
            return user_data
        # If it's a basic UserProfile or dict, upgrade it
        # ... logic ...
        return DeepUserProfile(**user_data.dict()) # Simplistic conversion

    def _notify_user(self, user_id: str, opp: Scholarship):
        """Publish match to User Notification Stream"""
        kafka_producer_manager.publish_to_stream(
            topic=KafkaConfig.TOPIC_USER_MATCHES,
            key=user_id,
            value={
                "type": "new_match",
                "opportunity_id": opp.id,
                "score": opp.match_score,
                "title": opp.title,
                "timestamp": opp.deadline_timestamp # or now
            }
        )

matching_worker = MatchingWorker()
