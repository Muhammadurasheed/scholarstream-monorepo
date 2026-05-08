
import structlog
import google.generativeai as genai
from typing import List, Optional, Any
from app.config import settings
from app.models import DeepUserProfile, OpportunitySchema

logger = structlog.get_logger()

# Configure Gemini
if settings.gemini_api_key:
    genai.configure(api_key=settings.gemini_api_key)

from vertexai.language_models import TextEmbeddingModel

class VectorizationService:
    """
    The 'Digital DNA' Generator.
    Converts DeepProfiles into Vector Embeddings for RAG.
    """
    
    MODEL_NAME = "text-embedding-004" # Latest Vertex AI Model

    async def vectorize_profile(self, profile: DeepUserProfile) -> Optional[List[float]]:
        """
        Generate a single vector embedding representing the user's entire professional identity.
        """
        # 1. Synthesize the "DNA" text
        dna_text = self._synthesize_dna(profile)
        
        try:
            # 2. Call Vertex AI
            model = TextEmbeddingModel.from_pretrained(self.MODEL_NAME)
            embeddings = model.get_embeddings([dna_text])
            
            vector = embeddings[0].values
            logger.info("Generated Digital DNA Vector (Vertex AI)", dimensions=len(vector))
            return vector

        except Exception as e:
            logger.error("Vertex AI Vectorization failed", error=str(e))
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
        Generate a vector embedding for an opportunity.
        """
        text = f"{opportunity.title} {opportunity.description} {' '.join(opportunity.geo_tags)} {' '.join(opportunity.type_tags)}"
        
        try:
            model = TextEmbeddingModel.from_pretrained(self.MODEL_NAME)
            embeddings = model.get_embeddings([text])
            return embeddings[0].values
        except Exception as e:
            logger.error("Opportunity vectorization failed", error=str(e))
            return None

    async def vectorize_query(self, query: str) -> Optional[List[float]]:
        """
        Generate embedding for a search query.
        """
        if not query or len(query.strip()) < 3:
            return None
        
        try:
            model = TextEmbeddingModel.from_pretrained(self.MODEL_NAME)
            # Use 'RETRIEVAL_QUERY' task for search queries
            embeddings = model.get_embeddings([query.strip()])
            
            vector = embeddings[0].values
            logger.info("Generated query embedding", query_preview=query[:50])
            return vector
            
        except Exception as e:
            logger.error("Query vectorization failed", error=str(e), query=query[:50])
            return None

# Singleton
vectorization_service = VectorizationService()
