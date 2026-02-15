"""
Cortex Matching Engine
The Heart of ScholarStream's Personalization.
Implements the "70/30" Match Formula:
Match Score = (Vector Similarity * 0.7) + (Heuristic Filters * 0.3)
"""
import uuid
import structlog
import math
from datetime import datetime
from typing import List, Optional, Dict, Any

from app.models import (
    Scholarship,
    UserProfile,
    DeepUserProfile,
    DiscoveryJobResponse
)
from app.services.scraper_service import scraper_service
from app.database import db
# from app.services.vectorization_service import vectorization_service # Circular import risk, import inside method

logger = structlog.get_logger()

class MatchingEngine:
    """
    The Cortex Brain.
    Decides what you see based on WHO you are (Vectors) and WHAT you need (Filters).
    """
    
    VECTOR_WEIGHT = 0.7
    FILTER_WEIGHT = 0.3

    async def calculate_match_score(self, opportunity: Scholarship, profile: DeepUserProfile) -> float:
        """
        The "Cortex Formula" implementation.
        """
        # 1. Vector Score (70%)
        vector_score = self._compute_vector_similarity(opportunity.embedding, profile.vector_id)
        # Note: profile.vector_id is a placeholder, we need the actual user vector.
        # Ideally, we fetch the user's vector from the DB or it's passed in.
        # For this implementation, let's assume we can fetch it or it's in the profile if we enhanced it.
        # If vector is missing, fallback to heuristics.
        
        # 2. Heuristic Filter Score (30%)
        filter_score = self._score_heuristics(opportunity, profile)
        
        if vector_score is None:
            # Fallback for non-vectorized users/opportunities
            return round(filter_score * 100, 1)

        final_score = (vector_score * self.VECTOR_WEIGHT * 100) + (filter_score * self.FILTER_WEIGHT * 100)
        return round(max(0, min(100, final_score)), 1)
    
    def _compute_vector_similarity(self, opp_vector: Optional[List[float]], user_vector: Optional[List[float]]) -> Optional[float]:
        """
        Cosine Similarity between User DNA and Opportunity DNA.
        """
        if not opp_vector or not user_vector:
            return None
            
        try:
            # Manual Dot Product & Magnitude (Avoid numpy dependency for now if not present)
            dot_product = sum(a * b for a, b in zip(opp_vector, user_vector))
            magnitude_a = math.sqrt(sum(a * a for a in opp_vector))
            magnitude_b = math.sqrt(sum(b * b for b in user_vector))
            
            if magnitude_a == 0 or magnitude_b == 0:
                return 0.0
                
            return dot_product / (magnitude_a * magnitude_b)
        except Exception:
            return None

    def _score_heuristics(self, opp: Scholarship, profile: DeepUserProfile) -> float:
        """
        Traditional hard-logic matching (Tags, Eligibility, Keywords).
        Returns 0.0 to 1.0
        """
        score = 0.5 # Baseline
        
        # 1. Keyword Overlap (Jaccard-ish)
        user_text = (f"{profile.major} {' '.join(profile.hard_skills)} {' '.join(profile.soft_skills)}").lower()
        opp_text = (f"{opp.title} {opp.description} {' '.join(opp.tags)}").lower()
        
        # Simple boost for matching terms
        priority_keywords = [w.strip() for w in user_text.split() if len(w) > 3]
        matches = sum(1 for w in priority_keywords if w in opp_text)
        
        if len(priority_keywords) > 0:
            keyword_boost = min(0.3, (matches / len(priority_keywords)) * 0.5)
            score += keyword_boost

        # 2. Location Match
        if hasattr(profile, 'location') and profile.location:
             if any(loc in str(opp.geo_tags) for loc in [profile.location, "Global", "Remote"]):
                 score += 0.1

        return min(1.0, score)

    async def batch_match(self, opportunities: List[Scholarship], profile: DeepUserProfile) -> List[Scholarship]:
        """
        Process a batch of opportunities against a user profile.
        """
        scored_opportunities = []
        
        # Retrieve user vector (Mocking this retrieval for now, in prod fetch from Vector DB)
        # For now, we assume the profile MIGHT have it implicitly or we fetch it.
        # Let's import the service to generate it on the fly if needed (caching needed in V2)
        from app.services.vectorization_service import vectorization_service
        user_vector = await vectorization_service.vectorize_profile(profile)

        for opp in opportunities:
            # Calculate Score
            try:
                # pass user_vector explicitly to avoid re-fetching
                vector_score = self._compute_vector_similarity(opp.embedding, user_vector)
                filter_score = self._score_heuristics(opp, profile)
                
                if vector_score is not None:
                     final_score = (vector_score * self.VECTOR_WEIGHT * 100) + (filter_score * self.FILTER_WEIGHT * 100)
                     opp.match_reasons.append(f"AI Match: {int(vector_score*100)}%")
                else:
                     final_score = filter_score * 100
                     opp.match_reasons.append("Heuristic Match")

                opp.match_score = round(max(0, min(100, final_score)), 1)
                
                # Filter Low Matches
                if opp.match_score >= 40: # Minimum viability
                     scored_opportunities.append(opp)
            
            except Exception as e:
                logger.error("Matching error", id=opp.id, error=str(e))
                continue

        # Sort by score
        return sorted(scored_opportunities, key=lambda x: x.match_score, reverse=True)

matching_engine = MatchingEngine()
