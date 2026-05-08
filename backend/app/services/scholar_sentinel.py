import structlog
import asyncio
from typing import List, Dict, Any
from datetime import datetime

from app.database import db
from app.models import UserProfile, Scholarship
from app.services.matching_service import matching_service
from app.services.gemma_matching_service import gemma_matching_service

logger = structlog.get_logger()

class ScholarSentinel:
    """
    Autonomous scouting engine.
    Patrols the web and database for new opportunities matching user profiles.
    """

    async def run_patrol_for_all_users(self):
        """
        Main job to run patrols for all users with patrol_enabled=True
        """
        logger.info("Starting Scholar Sentinel Global Patrol")
        
        try:
            # 1. Fetch all scholarships (the "Pool")
            all_scholarships = await db.get_all_scholarships()
            if not all_scholarships:
                logger.warning("No scholarships in pool to match against")
                return

            # 2. Fetch all users with patrol enabled
            # Note: We'll assume a db method exists to get patrolling users
            users = await db.get_patrolling_users()
            
            for user_data in users:
                user_id = user_data['id']
                profile = UserProfile(**user_data['profile'])
                
                logger.info("Patrolling for user", user_id=user_id, name=profile.name)
                await self.patrol_for_user(user_id, profile, all_scholarships)

        except Exception as e:
            logger.error("Global Patrol failed", error=str(e))

    async def patrol_for_user(self, user_id: str, profile: UserProfile, scholarship_pool: List[Scholarship]):
        """
        Evaluate the scholarship pool against a specific user profile
        """
        hits = []
        
        # We only want to notify about NEW high-potential matches
        # 1. Get existing matches to avoid duplicates
        existing_match_ids = await db.get_user_match_ids(user_id)
        
        for opp in scholarship_pool:
            if opp.id in existing_match_ids:
                continue
                
            # 2. Fast score (Personalization Engine)
            score = matching_service.calculate_match_score(opp, profile)
            
            # 3. If high potential (> 80), trigger Gemma 4 for "Deep Reasoning"
            if score >= 80:
                logger.info("High potential hit found by Sentinel", user_id=user_id, opp=opp.id)
                
                # Generate the Agentic Report (The Moat)
                report = await gemma_matching_service.generate_match_report(opp, profile)
                
                # If Gemma confirms the high match
                try:
                    gemma_score = float(report.get("score", 0))
                    if gemma_score >= 85:
                        hit = {
                            "scholarship_id": opp.id,
                            "name": opp.name or opp.title,
                            "score": gemma_score,
                            "reasoning": report.get("synthesis"),
                            "action_plan": report.get("action_plan"),
                            "found_at": datetime.now().isoformat(),
                            "status": "unread"
                        }
                        hits.append(hit)
                        
                        # Add to user matches immediately
                        await db.save_user_matches(user_id, [opp.id])
                except ValueError:
                    continue

        # 4. Save Sentinel Hits for the user to see in their Dashboard
        if hits:
            logger.info("Sentinel found hits for user", user_id=user_id, count=len(hits))
            await db.save_sentinel_hits(user_id, hits)
            # In a real app, this would trigger an Email/Push notification
            # await notification_service.send_match_alert(user_id, hits)

# Global instance
scholar_sentinel = ScholarSentinel()
