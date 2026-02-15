"""
Google Gemini AI Service
Handles AI-powered scholarship enrichment and matching
"""
import google.generativeai as genai
from typing import Dict, List, Optional, Any
import json
import asyncio
import structlog
from datetime import datetime, timedelta
import hashlib

try:
    from upstash_redis import Redis
    UPSTASH_AVAILABLE = True
except ImportError:
    UPSTASH_AVAILABLE = False
    Redis = None

from app.config import settings
from app.models import (
    ScrapedScholarship,
    UserProfile,
    ScholarshipEligibility,
    ScholarshipRequirements,
    AIEnrichmentResponse,
    MatchTier,
    PriorityLevel,
    CompetitionLevel
)

logger = structlog.get_logger()


class GeminiAIService:
    """Google Gemini AI integration for scholarship processing"""
    
    def __init__(self):
        """Initialize Gemini AI with Upstash Redis support"""
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model)
        
        # Initialize Upstash Redis for rate limiting and caching
        self.redis_client = None
        if UPSTASH_AVAILABLE and settings.upstash_redis_rest_url and settings.upstash_redis_rest_token:
            try:
                self.redis_client = Redis(
                    url=settings.upstash_redis_rest_url,
                    token=settings.upstash_redis_rest_token
                )
                logger.info("Upstash Redis initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Upstash Redis: {e}. Falling back to in-memory caching.")
                self.redis_client = None
        else:
            logger.warning("Upstash Redis not configured - using in-memory caching and rate limiting")
        
        # Fallback in-memory cache if Redis unavailable
        self.memory_cache: Dict[str, tuple] = {}
        
        # Rate limiting configuration
        self.rate_limit_key = "gemini_api_calls"
        self.rate_limit_window = 3600  # 1 hour in seconds
        self.max_calls_per_hour = settings.gemini_rate_limit_per_hour
        
        # In-memory rate limiter fallback
        self.rate_limiter = {
            'count': 0,
            'window_start': datetime.now(),
            'limit': settings.gemini_rate_limit_per_hour
        }
        
        logger.info(
            "Gemini AI Service initialized",
            model=settings.gemini_model,
            rate_limit=self.max_calls_per_hour,
            redis_enabled=self.redis_client is not None
        )
    
    def _check_rate_limit(self) -> bool:
        """
        Check if we're within rate limits
        Uses Upstash Redis if available, falls back to in-memory tracking
        """
        if self.redis_client:
            # Use Upstash Redis for distributed rate limiting
            try:
                current_calls = self.redis_client.get(self.rate_limit_key)
                
                if current_calls is None:
                    # First call in this window
                    self.redis_client.set(
                        self.rate_limit_key,
                        "1",
                        ex=self.rate_limit_window
                    )
                    return True
                
                current_calls_int = int(current_calls)
                if current_calls_int >= self.max_calls_per_hour:
                    logger.warning(
                        "Gemini rate limit exceeded (Redis)",
                        current_calls=current_calls_int,
                        max_calls=self.max_calls_per_hour
                    )
                    return False
                
                # Increment counter
                self.redis_client.incr(self.rate_limit_key)
                return True
                
            except Exception as e:
                logger.error(f"Redis rate limit check failed: {e}. Using in-memory fallback.")
                # Fall through to in-memory check
        
        # In-memory rate limiting fallback
        now = datetime.now()
        if (now - self.rate_limiter['window_start']) > timedelta(hours=1):
            # Reset window
            self.rate_limiter['count'] = 0
            self.rate_limiter['window_start'] = now
        
        if self.rate_limiter['count'] >= self.rate_limiter['limit']:
            logger.warning("Gemini rate limit exceeded (in-memory)")
            return False
        
        self.rate_limiter['count'] += 1
        return True

    def generate_content(self, prompt: str) -> Any:
        # ... (keep existing sync for compat)
        if not self._check_rate_limit():
            raise Exception("Rate limit exceeded")
        try:
            return self.model.generate_content(prompt).text
        except Exception as e:
            logger.error("Gemini generation failed", error=str(e))
            raise e

    async def generate_content_async(self, prompt: str) -> Any:
        """Async wrapper for generate_content"""
        if not self._check_rate_limit():
            raise Exception("Rate limit exceeded")
        
        try:
            # Use run_in_executor or the library's async method if available
            # Gemini 1.5 library has generate_content_async
            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            logger.error("Gemini async generation failed", error=str(e))
            raise e
    
    async def enrich_scholarship(
        self,
        scholarship: ScrapedScholarship,
        user_profile: UserProfile
    ) -> Optional[AIEnrichmentResponse]:
        """
        Use AI to parse and enrich scholarship data
        Extract structured eligibility, requirements, and calculate match score
        """
        # Check cache first
        cache_key = self._generate_cache_key(scholarship.source_url, user_profile.name)
        cached_enrichment = self._get_cached_enrichment(cache_key)
        if cached_enrichment:
            logger.info("Using cached AI enrichment", source=scholarship.source_url)
            return cached_enrichment
        
        # Check rate limit
        if not self._check_rate_limit():
            logger.error("Gemini API rate limit exceeded")
            return None
        
        try:
            prompt = self._build_enrichment_prompt(scholarship, user_profile)
            response = self.model.generate_content(prompt)
            
            # Parse AI response
            enriched_data = self._parse_ai_response(response.text)
            
            # Cache the result
            self._cache_enrichment(cache_key, enriched_data)
            
            logger.info("Scholarship enriched with AI", source=scholarship.source_url)
            return enriched_data
            
        except Exception as e:
            logger.error("AI enrichment failed", error=str(e), source=scholarship.source_url)
            return None
    
    def _build_enrichment_prompt(self, scholarship: ScrapedScholarship, user_profile: UserProfile) -> str:
        """Build prompt for AI to enrich scholarship data"""
        return f"""You are an expert scholarship analyst. Analyze this scholarship and provide structured data.

SCHOLARSHIP DATA:
Name: {scholarship.name}
Organization: {scholarship.organization}
Amount: ${scholarship.amount}
Deadline: {scholarship.deadline}
Description: {scholarship.description}
Eligibility (raw): {scholarship.eligibility_raw or 'Not specified'}
Requirements (raw): {scholarship.requirements_raw or 'Not specified'}

USER PROFILE:
Academic Status: {user_profile.academic_status}
School: {user_profile.school or 'Not specified'}
GPA: {user_profile.gpa or 'Not specified'}
Major: {user_profile.major or 'Not specified'}
Graduation Year: {user_profile.graduation_year or 'Not specified'}
Background: {', '.join(user_profile.background) if user_profile.background else 'Not specified'}
Financial Need: ${user_profile.financial_need or 'Not specified'}
Interests: {', '.join(user_profile.interests) if user_profile.interests else 'Not specified'}

TASK:
Provide a JSON response with the following structure (respond ONLY with valid JSON, no additional text):

{{
  "eligibility": {{
    "gpa_min": <float or null>,
    "grades_eligible": [<list of grade levels: "High School Senior", "Undergraduate", "Graduate", etc.>],
    "majors": [<list of eligible majors or null if any>],
    "gender": <string or null>,
    "citizenship": <string or null>,
    "backgrounds": [<list: "First-generation", "Minority", "LGBTQ+", "Low-income", "Veteran", etc.>],
    "states": [<list of state codes or null if nationwide>]
  }},
  "requirements": {{
    "essay": <true/false>,
    "essay_prompts": [<list of essay prompts if applicable>],
    "recommendation_letters": <integer count>,
    "transcript": <true/false>,
    "resume": <true/false>,
    "other": [<list of other requirements>]
  }},
  "tags": [<3-5 relevant tags like "STEM", "Need-Based", "Merit-Based", "Leadership", etc.>],
  "match_score": <0-100 integer representing how well this user matches this scholarship>,
  "match_tier": <"Excellent" (80-100), "Good" (60-79), "Fair" (40-59), or "Poor" (0-39)>,
  "priority_level": <"URGENT" if deadline <7 days, "HIGH" if high match, "MEDIUM" if moderate match, "LOW" otherwise>,
  "competition_level": <"Low", "Medium", or "High" based on requirements and award amount>,
  "estimated_time": <string like "2 hours", "4-6 hours", based on requirements complexity>
}}

Calculate match_score based on:
- GPA match (0-25 points)
                - Interest alignment (0-15 points)
                - Financial need match (0-15 points)

Respond with ONLY the JSON object, no markdown formatting or additional text."""

    async def analyze_query_intent(self, user_query: str) -> Dict[str, Any]:
        """
        The "Emergency" Query Strategy.
        Detects urgency ("fees due", "deadline", "urgent") and filters accordingly.
        """
        if not settings.gemini_api_key:
             return {"is_urgent": False, "filters": {}, "vector_query": user_query}

        prompt = f"""
        Analyze this student query: "{user_query}"
        
        Determine:
        1. Is this URGENT? (Deadline < 14 days, fees due, eviction risk, starvation)
        2. What are the key entities? (Location, Role, Domain)
        3. What type of finding is best? (Grant/Bounty = Fast, Scholarship = Slow)

        Return JSON only:
        {{
            "is_urgent": <bool>,
            "suggested_filters": {{
                "priority_level": "URGENT" (if urgent),
                "type_tags": ["Grant", "Bounty"] (if urgent),
                "deadline_days_max": 14 (if urgent)
            }},
            "vector_search_query": <Optimized search string, e.g. "Software grants Nigeria fast funding">
        }}
        """
        
        try:
            response = await self.generate_content_async(prompt)
            data = self._parse_json_safe(response) # Helper needed
            return data
        except Exception as e:
            logger.error("Intent analysis failed", error=str(e))
            # Fallback
            is_urgent = any(w in user_query.lower() for w in ["urgent", "deadline", "fees", "asap"])
            return {
                "is_urgent": is_urgent,
                "filters": {"priority_level": "URGENT"} if is_urgent else {},
                "vector_query": user_query
            }

    def _parse_json_safe(self, text: str) -> Dict:
        """Helper to clean and parse JSON from LLM"""
        text = text.strip()
        if text.startswith('```json'): text = text[7:]
        if text.startswith('```'): text = text[3:]
        if text.endswith('```'): text = text[:-3]
        return json.loads(text.strip())

    
    def _parse_ai_response(self, response_text: str) -> AIEnrichmentResponse:
        """Parse AI response into structured data"""
        try:
            # Use helper
            data = self._parse_json_safe(response_text)
            
            # Validate and create structured response
            return AIEnrichmentResponse(
                eligibility=ScholarshipEligibility(**data.get('eligibility', {})),
                requirements=ScholarshipRequirements(**data.get('requirements', {})),
                tags=data.get('tags', []),
                match_score=float(data.get('match_score', 0)),
                match_tier=data.get('match_tier', "Fair"),
                priority_level=data.get('priority_level', "MEDIUM"),
                competition_level=data.get('competition_level', "Medium"),
                estimated_time=data.get('estimated_time', "2 hours")
            )
            
        except Exception as e:
            logger.error("Failed to parse AI response", error=str(e), response=response_text[:200])
            # Return default data if parsing fails
            return AIEnrichmentResponse(
                eligibility=ScholarshipEligibility(),
                requirements=ScholarshipRequirements(),
                tags=[],
                match_score=50.0,
                match_tier="Fair",
                priority_level="MEDIUM",
                competition_level="Medium",
                estimated_time="2-3 hours"
            )
    
    def _generate_cache_key(self, source_url: str, user_name: str) -> str:
        """Generate a unique cache key for scholarship + user combination"""
        key_string = f"{source_url}_{user_name}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cached_enrichment(self, cache_key: str) -> Optional[AIEnrichmentResponse]:
        """Get cached AI enrichment result from Redis or memory"""
        # Try Redis first
        if self.redis_client:
            try:
                cached = self.redis_client.get(f"ai_enrichment:{cache_key}")
                if cached:
                    logger.info("Cache hit (Redis)", cache_key=cache_key)
                    # Parse JSON string back to model
                    data = json.loads(cached)
                    return AIEnrichmentResponse(**data)
            except Exception as e:
                logger.error(f"Redis cache retrieval failed: {e}")
        
        # Fallback to in-memory cache
        if cache_key in self.memory_cache:
            cached_data, cached_time = self.memory_cache[cache_key]
            cache_age_hours = (datetime.now() - cached_time).total_seconds() / 3600
            if cache_age_hours < settings.ai_enrichment_cache_ttl_hours:
                logger.info("Cache hit (memory)", cache_key=cache_key)
                return cached_data
        
        return None
    
    def _cache_enrichment(self, cache_key: str, enrichment: AIEnrichmentResponse):
        """Cache AI enrichment result to Redis and memory"""
        # Store in Redis if available
        if self.redis_client:
            try:
                cache_ttl_seconds = settings.ai_enrichment_cache_ttl_hours * 3600
                # Convert to dict then to JSON for storage
                enrichment_dict = enrichment.model_dump()
                self.redis_client.set(
                    f"ai_enrichment:{cache_key}",
                    json.dumps(enrichment_dict),
                    ex=int(cache_ttl_seconds)
                )
                logger.info("Cached in Redis", cache_key=cache_key, ttl_hours=settings.ai_enrichment_cache_ttl_hours)
            except Exception as e:
                logger.error(f"Redis cache storage failed: {e}")
        
        # Also store in memory cache as backup
        self.memory_cache[cache_key] = (enrichment, datetime.now())
        logger.info("Cached in memory", cache_key=cache_key)
    
    async def batch_enrich_scholarships(
        self,
        scholarships: List[ScrapedScholarship],
        user_profile: UserProfile,
        batch_size: int = 5
    ) -> List[Optional[AIEnrichmentResponse]]:
        """
        Batch process multiple scholarships
        Process in batches to optimize API usage
        """
        results = []
        
        for i in range(0, len(scholarships), batch_size):
            batch = scholarships[i:i + batch_size]
            logger.info("Processing scholarship batch", batch_num=i//batch_size + 1)
            
            for scholarship in batch:
                enriched = await self.enrich_scholarship(scholarship, user_profile)
                results.append(enriched)
            
            # Brief pause between batches to respect rate limits
            if i + batch_size < len(scholarships):
                await asyncio.sleep(1)
        
        return results


# Global AI service instance
ai_service = GeminiAIService()
