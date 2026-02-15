"""
Opportunity Matching Service (Legacy API Wrapper)
Provides backward-compatible discovery job handling.
Internally uses MatchingEngine for scoring.
"""
import uuid
from typing import List, Optional, Dict, Any
import structlog
from datetime import datetime

from app.models import (
    Scholarship,
    UserProfile,
    DiscoveryJobResponse
)
from app.services.scraper_service import scraper_service
from app.database import db

logger = structlog.get_logger()


class OpportunityMatchingService:
    """Orchestrates multi-opportunity discovery and matching"""
    
    async def start_discovery_job(
        self,
        user_id: str,
        user_profile: UserProfile
    ) -> DiscoveryJobResponse:
        """
        Starts discovery process. Returns immediate results if cached,
        or creates a job and returns 'processing' status.
        """
        job_id = str(uuid.uuid4())
        
        try:
            # Step 1: Check cache (Fast path)
            cached_opportunities = await db.get_all_scholarships()
            
            if cached_opportunities:
                matched = self._filter_and_rank(cached_opportunities, user_profile)
                if matched:
                    scholarship_ids = [s.id for s in matched]
                    await db.save_user_matches(user_id, scholarship_ids)
                    
                    logger.info("Returning cached opportunities", count=len(matched))
                    
                    return DiscoveryJobResponse(
                        status="completed",
                        immediate_results=matched[:30],
                        job_id=job_id,
                        estimated_completion=0,
                        total_found=len(matched)
                    )
            
            # Step 2: Start fresh discovery (Slow path)
            await db.create_discovery_job(user_id, job_id)
            
            return DiscoveryJobResponse(
                status="processing",
                immediate_results=[],
                job_id=job_id,
                estimated_completion=15,
                total_found=0
            )
            
        except Exception as e:
            logger.error("Failed to start discovery job", error=str(e))
            raise

    async def run_background_discovery(
        self,
        job_id: str,
        user_id: str,
        user_profile: UserProfile
    ):
        """Background task for scraping and matching"""
        try:
            logger.info("Starting background discovery", job_id=job_id)
            
            # Step 3: Scrape ALL opportunity types
            raw_opportunities = await scraper_service.discover_all_opportunities(
                user_profile.model_dump()
            )
            
            logger.info("Scraping complete", count=len(raw_opportunities))
            
            # Step 4: Convert to Scholarship objects
            opportunities = []
            for opp_data in raw_opportunities:
                try:
                    scholarship = self._convert_to_scholarship(opp_data, user_profile)
                    if scholarship:
                        opportunities.append(scholarship)
                except Exception as e:
                    logger.error("Failed to convert opportunity", error=str(e))
            
            # Step 5: Filter and rank
            matched_opportunities = self._filter_and_rank(opportunities, user_profile)
            
            # Step 6: Store in database
            for opp in matched_opportunities:
                await db.save_scholarship(opp)
            
            scholarship_ids = [s.id for s in matched_opportunities]
            await db.save_user_matches(user_id, scholarship_ids)
            
            # Update job status
            await db.update_job_status(
                job_id=job_id,
                status="completed",
                scholarships_found=len(matched_opportunities)
            )
            
            logger.info("Background discovery complete", total=len(matched_opportunities))
            
        except Exception as e:
            logger.error("Background discovery failed", error=str(e), job_id=job_id)
            await db.update_job_status(job_id, "failed", 0)
    
    def _convert_to_scholarship(self, opp_data: Dict[str, Any], user_profile: UserProfile) -> Optional[Scholarship]:
        """Convert raw opportunity to Scholarship model"""
        from app.services.opportunity_converter import convert_to_scholarship
        return convert_to_scholarship(opp_data, user_profile)
    
    def calculate_match_score(self, opportunity: Scholarship, profile: UserProfile) -> float:
        """Use PersonalizationEngine for proper scoring"""
        from app.services.personalization_engine import personalization_engine
        
        # Convert Scholarship to dict for personalization engine
        opp_dict = {
            'name': opportunity.name or opportunity.title or 'Unknown Opportunity',
            'description': opportunity.description or '',
            'organization': opportunity.organization or '',
            'tags': opportunity.tags if hasattr(opportunity, 'tags') else [],
            'eligibility': opportunity.eligibility.model_dump() if hasattr(opportunity.eligibility, 'model_dump') else {},
            'requirements': opportunity.requirements.model_dump() if hasattr(opportunity.requirements, 'model_dump') else {},
        }
        
        return personalization_engine.calculate_personalized_score(opp_dict, profile)
    
    def _filter_and_rank(
        self,
        opportunities: List[Scholarship],
        user_profile: UserProfile
    ) -> List[Scholarship]:
        """Filter and rank opportunities using PersonalizationEngine"""
        from datetime import datetime
        
        eligible = []
        now = datetime.now().timestamp()
        
        for opp in opportunities:
            # Skip expired
            if hasattr(opp, 'deadline_timestamp') and opp.deadline_timestamp:
                if opp.deadline_timestamp < int(now):
                    continue
            
            # Calculate score using PersonalizationEngine
            score = self.calculate_match_score(opp, user_profile)
            opp.match_score = int(round(score))
            
            # Determine match tier
            opp.match_tier = self.get_match_tier(opp.match_score)
            
            # Include all opportunities (minimum 10% ensured by personalization engine)
            eligible.append(opp)
        
        return sorted(eligible, key=lambda x: x.match_score, reverse=True)

    def get_match_tier(self, score: float) -> str:
        """Convert match score to tier"""
        if score >= 85:
            return "Excellent"
        elif score >= 70:
            return "Good"  
        elif score >= 55:
            return "Fair"
        else:
            return "Poor"
    
    async def get_job_status(self, job_id: str) -> Optional[DiscoveryJobResponse]:
        """Get discovery job progress"""
        job_data = await db.get_discovery_job(job_id)
        
        if not job_data:
            return None
        
        return DiscoveryJobResponse(
            status=job_data['status'],
            progress=job_data.get('progress', 100.0),
            total_found=job_data['scholarships_found']
        )


# Global matching service instance
matching_service = OpportunityMatchingService()
