import structlog
from typing import List, Dict, Any
from app.services.gemma_service import gemma_service
from app.database import db

logger = structlog.get_logger()

class EvidenceEngine:
    """
    The 'Evidence' extraction engine.
    Extracts high-impact quotes and stats from user documents (Resume, Papers)
    to be used by the Agentic Co-pilot during applications.
    """

    async def extract_evidence_from_text(self, text: str, doc_type: str = "resume") -> List[Dict[str, Any]]:
        """
        Uses Gemma 4 to extract specific 'Evidence Snippets' from a document.
        """
        prompt = f"""
        You are an elite Application Specialist.
        Analyze the following {doc_type} and extract 3-5 'Evidence Snippets' that would impress a scholarship committee.
        
        ### CRITERIA FOR SNIPPETS:
        1. Must be specific (stats, specific tech, leadership roles).
        2. Must be verbatim quotes where possible.
        3. Focus on impact and results.
        
        ### DOCUMENT TEXT:
        {text[:4000]}
        
        ### RESPONSE FORMAT (JSON-like list):
        - [Snippet]: "Led a team of 5 to win the Lagos Hackathon" (Category: Leadership)
        - [Snippet]: "Built a Computer Vision model with 94% accuracy" (Category: Technical)
        """

        try:
            logger.info("Extracting evidence snippets", doc_type=doc_type)
            result = await gemma_service.generate_content_async(prompt)
            
            # Simple parsing for the demo (in production we'd use structured output)
            lines = result.get('text', '').split('\n')
            snippets = []
            for line in lines:
                if '[Snippet]:' in line:
                    snippets.append({
                        "text": line.split('[Snippet]:')[1].strip(),
                        "source_type": doc_type
                    })
            
            return snippets

        except Exception as e:
            logger.error("Evidence extraction failed", error=str(e))
            return []

    async def get_relevant_evidence(self, user_id: str, query: str) -> List[str]:
        """
        Retrieves evidence snippets relevant to a specific application question.
        """
        # MVP: Get all evidence for the user
        # Production: Use semantic search over evidence chunks
        try:
            user_data = await db.get_user_profile(user_id)
            evidence = user_data.get('evidence_bank', [])
            
            if not evidence:
                return []
            
            # Simple keyword filtering for now
            relevant = [e['text'] for e in evidence if any(word.lower() in e['text'].lower() for word in query.split())]
            
            # If nothing matches, return top 3
            return relevant[:3] if relevant else [e['text'] for e in evidence[:3]]

        except Exception as e:
            logger.error("Failed to fetch evidence", error=str(e))
            return []

# Singleton
evidence_engine = EvidenceEngine()
