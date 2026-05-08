
import structlog
import google.generativeai as genai
from typing import List, Optional, Any
from app.config import settings
from app.models import DeepUserProfile, OpportunitySchema

logger = structlog.get_logger()

# Configure Gemini
if settings.gemini_api_key:
    genai.configure(api_key=settings.gemini_api_key)

class VectorizationService:
    """
    The 'Digital DNA' Generator.
    Converts DeepProfiles into Vector Embeddings for RAG.
    """
    
    MODEL_NAME = "models/embedding-001"

    async def vectorize_profile(self, profile: DeepUserProfile) -> Optional[List[float]]:
        """
        Generate a single vector embedding representing the user's entire professional identity.
        Combines Bio, Skills, and Projects into a rich text representation first.
        """
        if not settings.gemini_api_key:
            logger.warning("Vectorization skipped: No Gemini API Key")
            return None

        # 1. Synthesize the "DNA" text
        dna_text = self._synthesize_dna(profile)
        
        try:
            # 2. Call Gemini
            result = genai.embed_content(
                model=self.MODEL_NAME,
                content=dna_text,
                task_type="retrieval_document",
                title="User Professional Profile"
            )
            
            embedding = result['embedding']
            logger.info("Generated Digital DNA Vector", dimensions=len(embedding))
            return embedding

        except Exception as e:
            logger.error("Vectorization failed", error=str(e))
            return None

    def _synthesize_dna(self, profile: DeepUserProfile) -> str:
        """
        Converts structured profile into a semantic narrative for the LLM.
        """
        parts = [
            f"Candidate Name: {profile.name}",
            f"Bio: {profile.bio}",
            f"Role: {profile.major or 'Student'} at {profile.school}",
            f"Core Competencies: {', '.join(profile.hard_skills)}",
            f"Soft Skills: {', '.join(profile.soft_skills)}",
            "Portfolio Highlights:"
        ]
        
        for p in profile.projects:
            parts.append(f"- {p.title}: {p.description} (Stack: {', '.join(p.tech_stack)})")
            
        for w in profile.experience:
            parts.append(f"- {w.role} at {w.company}: {w.description}")
            
        return "\n".join(parts)

    async def vectorize_opportunity(self, opportunity: OpportunitySchema) -> Optional[List[float]]:
        """
        Geneate a vector embedding for an opportunity.
        """
        if not settings.gemini_api_key:
            return None
            
        # Synthesize text for embedding
        text = f"{opportunity.title} {opportunity.description} {' '.join(opportunity.geo_tags)} {' '.join(opportunity.type_tags)}"
        
        try:
            result = genai.embed_content(
                model=self.MODEL_NAME,
                content=text,
                task_type="retrieval_document",
                title=opportunity.title
            )
            return result['embedding']
        except Exception as e:
            logger.error("Opportunity vectorization failed", error=str(e))
            return None

    async def vectorize_query(self, query: str) -> Optional[List[float]]:
        """
        Generate embedding for a search query.
        Uses retrieval_query task type for optimal search performance.
        
        This is used by the AI chat to enable semantic search over opportunities.
        """
        if not settings.gemini_api_key:
            logger.warning("Query vectorization skipped: No Gemini API Key")
            return None
        
        if not query or len(query.strip()) < 3:
            return None
        
        try:
            result = genai.embed_content(
                model=self.MODEL_NAME,
                content=query.strip(),
                task_type="retrieval_query"  # Optimized for search queries
            )
            
            embedding = result['embedding']
            logger.info("Generated query embedding", query_preview=query[:50], dimensions=len(embedding))
            return embedding
            
        except Exception as e:
            logger.error("Query vectorization failed", error=str(e), query=query[:50])
            return None

# Singleton
vectorization_service = VectorizationService()
