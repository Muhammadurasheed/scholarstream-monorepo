"""
Personalization Engine V2 - Deep Semantic Matching
Transforms ScholarStream from generic to AI-powered personalization
FIXED: Duplicate method bug, 30% floor removed, semantic scoring added
"""
from typing import Dict, Any, List, Optional
import structlog
import asyncio

logger = structlog.get_logger()


class PersonalizationEngine:
    """Advanced personalization using semantic matching and behavioral signals"""
    
    def __init__(self):
        # Interest-to-keyword mapping for intelligent matching
        self.interest_keywords = {
            'artificial intelligence': ['AI', 'machine learning', 'deep learning', 'neural networks', 'NLP', 'computer vision', 'GPT', 'LLM', 'generative AI'],
            'web development': ['web', 'frontend', 'backend', 'fullstack', 'React', 'Node.js', 'JavaScript', 'TypeScript', 'Next.js', 'Vue', 'Angular'],
            'cybersecurity': ['security', 'hacking', 'penetration testing', 'bug bounty', 'CTF', 'cryptography', 'ethical hacking', 'infosec'],
            'data science': ['data', 'analytics', 'statistics', 'visualization', 'pandas', 'numpy', 'data analysis', 'big data', 'ML'],
            'mobile development': ['mobile', 'iOS', 'Android', 'React Native', 'Flutter', 'Swift', 'Kotlin', 'app development'],
            'blockchain': ['blockchain', 'cryptocurrency', 'Web3', 'smart contracts', 'Ethereum', 'Solidity', 'DeFi', 'NFT', 'crypto'],
            'game development': ['game', 'Unity', '3D', 'graphics', 'Unreal Engine', 'game design', 'gaming', 'gamedev'],
            'robotics': ['robotics', 'automation', 'embedded systems', 'Arduino', 'ROS', 'mechatronics', 'IoT', 'hardware'],
            'healthcare tech': ['healthcare', 'medical', 'biotech', 'health informatics', 'telemedicine', 'healthtech', 'biomedical'],
            'fintech': ['finance', 'banking', 'payments', 'trading', 'financial technology', 'fintech', 'defi'],
            'social impact': ['social good', 'nonprofit', 'education', 'accessibility', 'sustainability', 'impact', 'climate'],
            'entrepreneurship': ['startup', 'business', 'innovation', 'venture', 'founder', 'entrepreneur', 'pitch'],
            'cloud computing': ['cloud', 'AWS', 'Azure', 'GCP', 'serverless', 'DevOps', 'infrastructure', 'kubernetes'],
            'ui/ux design': ['design', 'UI', 'UX', 'user experience', 'Figma', 'product design', 'interface', 'prototype'],
            # Direct User Inputs (common shorthand)
            'ai': ['AI', 'artificial intelligence', 'machine learning', 'LLM', 'GPT', 'neural', 'generative'],
            'coding': ['coding', 'software', 'programming', 'development', 'code', 'engineer', 'developer', 'script'],
            'python': ['python', 'django', 'flask', 'fastapi', 'pandas', 'pytorch', 'tensorflow', 'scikit'],
            'hackathons': ['hackathon', 'hack', 'build', 'competition', 'sprint', 'devpost', 'mlh'],
            'software': ['software', 'engineering', 'developer', 'SaaS', 'tech', 'backend', 'frontend'],
            'math': ['math', 'mathematics', 'statistics', 'calculus', 'algebra', 'quantitative'],
            'design': ['design', 'ui', 'ux', 'product', 'figma', 'creative', 'graphics'],
        }
        self._gemini_client = None
    
    def _get_attr(self, obj: Any, attr: str, default: Any = None) -> Any:
        """Helper to get attribute from object or key from dict"""
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return getattr(obj, attr, default)

    def _safe_get_dict(self, data: Dict[str, Any], key: str) -> Dict[str, Any]:
        """Safely get a nested dict, handling cases where it might be a string"""
        val = data.get(key)
        if isinstance(val, dict):
            return val
        return {}

    def calculate_personalized_score(
        self, 
        opportunity: Dict[str, Any], 
        user_profile: Any
    ) -> float:
        """
        Calculate personalized match score (0-100)
        V2: REMOVED 30% FLOOR - Scores now range from 0-100 based on true fit
        """
        score = 0.0
        max_score = 100.0
        
        # 1. Interest Match (40 points max) - MOST IMPORTANT
        interest_score = self._score_interests(opportunity, user_profile)
        score += interest_score * 0.4
        
        # 2. Passion Alignment (30 points max)
        passion_score = self._score_passions(opportunity, user_profile)
        score += passion_score * 0.3
        
        # 3. Demographic Match (20 points max)
        demographic_score = self._score_demographics(opportunity, user_profile)
        score += demographic_score * 0.2
        
        # 4. Academic Fit (10 points max)
        academic_score = self._score_academics(opportunity, user_profile)
        score += academic_score * 0.1
        
        try:
             opp_name = opportunity.get('name') or opportunity.get('title') or 'Unknown'
             logger.info(
                "Personalization V2 Score",
                opportunity=opp_name[:50],
                interest=int(interest_score),
                passion=int(passion_score),
                demographic=int(demographic_score),
                academic=int(academic_score),
                final=int(score)
             )
        except Exception:
             pass
        
        # V2 FIX: NO ARTIFICIAL FLOOR - Return true dynamic score
        user_interests = self._get_attr(user_profile, 'interests') or []
        if not user_interests:
            # Empty profile: return actual calculated score (no floor)
            # This encourages users to complete their profile
            return float(int(max(min(score, max_score), 5.0)))  # 5% minimum for UI display
        
        # For users with profiles, show true calculated score
        return float(int(max(min(score, max_score), 5.0)))
    
    def _score_interests(self, opp: Dict[str, Any], profile: Any) -> float:
        """Score based on user interests (0-100) - FIXED: No duplicate definition"""
        interests = self._get_attr(profile, 'interests') or []
        
        if not interests:
            return 50.0  # Neutral score if no interests
        
        user_interests = [str(i).lower().strip() for i in interests]
        opp_text = self._get_opportunity_text(opp).lower()
        
        satisfied_interests = 0
        matched_details = []
        
        for interest in user_interests:
            # Get keywords for this interest (expand synonyms)
            keywords = self.interest_keywords.get(interest, [interest])
            
            # Check if ANY keyword matches (Interest Satisfied)
            if any(keyword.lower() in opp_text for keyword in keywords):
                satisfied_interests += 1
                matched_details.append(interest)
            # Also check if the raw interest term appears
            elif interest in opp_text:
                satisfied_interests += 1
                matched_details.append(interest)
        
        if not user_interests:
            return 50.0
        
        # Calculate match rate: % of User's Interests found in Opportunity
        match_rate = satisfied_interests / len(user_interests)
        
        # Boost: If more than 50% of interests match, boost by 1.3x
        if match_rate > 0.5:
            # High alignment boost
            match_rate = min(match_rate * 1.5, 1.0)
        
        # Boost: If more than 75% match, it's an elite fit
        if match_rate > 0.75:
            match_rate = min(match_rate * 1.2, 1.0)
            
        # V2 FIX: REMOVED 60% FLOOR - True dynamic scoring
        # If user has interests but none match, score should be low (not artificially boosted)
        # Only give a small boost (20%) if at least one interest matches
        if satisfied_interests > 0 and match_rate < 0.2:
            match_rate = 0.2  # Minimal match = 20%, not 60%
            
        logger.debug(
            "Interest scoring V2 - DYNAMIC",
            user_interests=user_interests,
            matched=matched_details,
            satisfied=satisfied_interests,
            rate=round(match_rate, 2)
        )
        
        return match_rate * 100
    
    def _score_passions(self, opp: Dict[str, Any], profile: Any) -> float:
        """Score based on user passions/background (0-100)"""
        background = self._get_attr(profile, 'background') or []
        
        if not background:
            return 50.0
        
        opp_text = self._get_opportunity_text(opp).lower()
        
        # Check for passion matches
        passion_matches = 0
        for passion in background:
            if isinstance(passion, str):
                # Check direct match
                if passion.lower() in opp_text:
                    passion_matches += 1
                # Check keyword expansion
                expanded = self.interest_keywords.get(passion.lower(), [])
                if any(kw.lower() in opp_text for kw in expanded):
                    passion_matches += 1
        
        if len(background) == 0:
            return 50.0
        
        match_rate = min(passion_matches / len(background), 1.0)
        return match_rate * 100
    
    def _score_demographics(self, opp: Dict[str, Any], profile: Any) -> float:
        """Score based on demographic match (0-100)"""
        score = 0.0
        checks = 0
        
        eligibility = self._safe_get_dict(opp, 'eligibility')
        
        # GPA check
        gpa_min = eligibility.get('gpa_min')
        user_gpa = self._get_attr(profile, 'gpa')
        
        if gpa_min and user_gpa:
            checks += 1
            if user_gpa >= gpa_min:
                score += 100
            elif user_gpa >= (gpa_min - 0.3):
                score += 50
        
        # Major check
        required_majors = eligibility.get('majors')
        user_major = self._get_attr(profile, 'major')
        
        if required_majors and user_major:
            checks += 1
            if any(major.lower() in user_major.lower() for major in required_majors):
                score += 100
            elif any(user_major.lower() in major.lower() for major in required_majors):
                score += 80  # Partial match
        elif not required_majors:
            # Open to all majors
            checks += 1
            score += 80
        
        # Background check
        required_backgrounds = eligibility.get('backgrounds', [])
        user_background = self._get_attr(profile, 'background') or []
        
        if required_backgrounds and user_background:
            checks += 1
            if any(bg in required_backgrounds for bg in user_background):
                score += 100
        
        # Location check (Global opportunities score well)
        geo_tags = opp.get('geo_tags', [])
        user_country = self._get_attr(profile, 'country')
        
        if geo_tags:
            checks += 1
            if 'Global' in geo_tags or 'International' in geo_tags:
                score += 90  # Global = accessible
            elif user_country and user_country in geo_tags:
                score += 100  # Location match
            else:
                score += 30  # Location mismatch
        
        return (score / checks) if checks > 0 else 60.0
    
    def _score_academics(self, opp: Dict[str, Any], profile: Any) -> float:
        """Score based on academic fit (0-100)"""
        score = 0.0
        
        # Academic status match
        academic_status = self._get_attr(profile, 'academic_status')
        
        if academic_status:
            eligibility = self._safe_get_dict(opp, 'eligibility')
            grade_levels = eligibility.get('grade_levels', []) or eligibility.get('grades_eligible', [])
            
            if not grade_levels:
                # Open to all academic levels
                return 70.0
            
            academic_status_lower = academic_status.lower()
            
            if academic_status in grade_levels:
                score += 100
            elif any(level.lower() in academic_status_lower for level in grade_levels):
                score += 80
            elif any(academic_status_lower in level.lower() for level in grade_levels):
                score += 70
            else:
                score += 20  # No match but not disqualifying
        else:
            score = 50.0  # No academic info, neutral
        
        return score
    
    def _get_opportunity_text(self, opp: Dict[str, Any]) -> str:
        """Get all searchable text from opportunity"""
        parts = [
            opp.get('name', ''),
            opp.get('title', ''),
            opp.get('description', ''),
            opp.get('organization', ''),
            ' '.join(opp.get('tags', [])),
            ' '.join(opp.get('type_tags', [])),
            ' '.join(opp.get('geo_tags', [])),
            opp.get('eligibility_text', ''),
        ]
        
        # Add requirements text
        requirements = self._safe_get_dict(opp, 'requirements')
        skills = requirements.get('skills_needed', [])
        if skills:
            parts.append(' '.join(skills))
        
        return ' '.join(filter(None, parts))

    async def calculate_semantic_score(
        self, 
        opportunity: Dict[str, Any], 
        user_profile: Any
    ) -> float:
        """
        V2 ENHANCEMENT: Use Gemini embeddings for semantic matching.
        Fallback to keyword matching if embeddings unavailable.
        """
        try:
            from app.services.ai_service import ai_service
            
            # Build user profile text
            interests = self._get_attr(user_profile, 'interests') or []
            background = self._get_attr(user_profile, 'background') or []
            major = self._get_attr(user_profile, 'major') or ''
            
            user_text = f"""
            Interests: {', '.join(interests)}
            Background: {', '.join(background)}
            Major: {major}
            """
            
            opp_text = self._get_opportunity_text(opportunity)
            
            # Use Gemini to score semantic similarity (0-100)
            prompt = f"""
            Rate the match between this user profile and opportunity on a scale of 0-100.
            Only output a single integer number, nothing else.
            
            USER PROFILE:
            {user_text}
            
            OPPORTUNITY:
            {opp_text[:2000]}
            
            Score (0-100):
            """
            
            result = await ai_service.generate_content_async(prompt)
            score = float(result.strip())
            return max(0, min(100, score))
            
        except Exception as e:
            logger.warning("Semantic scoring failed, falling back to keyword", error=str(e))
            return self.calculate_personalized_score(opportunity, user_profile)


# Global instance
personalization_engine = PersonalizationEngine()
