import structlog
from typing import Dict, Any, Optional
from app.services.gemma_service import gemma_service
from app.models import Scholarship, UserProfile

logger = structlog.get_logger()

class GemmaMatchingService:
    """
    Advanced agentic matching using Gemma 4 Thinking Mode.
    Provides deep qualitative analysis beyond simple keyword scores.
    """

    async def generate_match_report(
        self, 
        opportunity: Scholarship, 
        user_profile: UserProfile
    ) -> Dict[str, Any]:
        """
        Generates a comprehensive 'Counselor Report' using Gemma 4.
        """
        try:
            # Build profile summary
            interests = user_profile.interests or []
            background = user_profile.background or []
            major = user_profile.major or 'N/A'
            gpa = user_profile.gpa or 'N/A'
            
            profile_text = f"""
            Name: {user_profile.full_name or 'Student'}
            Major: {major}
            GPA: {gpa}
            Interests: {', '.join(interests)}
            Background/Experience: {', '.join(background)}
            Academic Status: {user_profile.academic_status or 'N/A'}
            Location: {user_profile.country or 'N/A'}
            """

            # Build opportunity summary
            opp_text = f"""
            Title: {opportunity.name or opportunity.title}
            Organization: {opportunity.organization or 'Unknown'}
            Description: {opportunity.description or 'N/A'}
            Eligibility: {opportunity.eligibility_text or 'N/A'}
            Value: {opportunity.amount or 'Varies'}
            Deadline: {opportunity.deadline or 'Varies'}
            """

            # Prompt for Gemma 4 (Einstein Counselor Persona)
            prompt = f"""
            You are a world-class Scholarship Counselor with Einstein-level intelligence and deep empathy.
            Your task is to analyze the match between this STUDENT and this OPPORTUNITY.
            
            STUDENT PROFILE:
            {profile_text}
            
            OPPORTUNITY DETAILS:
            {opp_text}
            
            ### INSTRUCTIONS:
            1. Use your 'Thinking Mode' to evaluate the deep alignment. Consider nuances like location, specific technical skills, and career trajectory.
            2. Provide your final analysis in a structured JSON-like format (but valid string response).
            3. Be brutally honest but encouraging.
            
            ### RESPONSE FORMAT:
            MATCH_SCORE: [0-100]
            SYNTHESIS: [1-2 sentences on why this fits or doesn't]
            THE_GAP: [What the student is missing or needs to emphasize]
            ACTION_PLAN: [3 specific, actionable steps to win this]
            """

            logger.info("Generating Gemma Match Report", opportunity=opportunity.id)
            
            # Call Gemma 4 via our specialized service
            result = await gemma_service.generate_content_async(
                prompt=prompt,
                stream=False
            )
            
            # Parse the response (Gemma returns Thinking block + Text)
            # Our service already separates them if possible, but here we parse the text part
            text_part = result.get('text', '')
            thinking_part = result.get('thinking', '')

            # Extract structured parts using basic parsing
            report = {
                "score": self._extract_value(text_part, "MATCH_SCORE:"),
                "synthesis": self._extract_value(text_part, "SYNTHESIS:"),
                "gap": self._extract_value(text_part, "THE_GAP:"),
                "action_plan": self._extract_value(text_part, "ACTION_PLAN:"),
                "thinking_process": thinking_part
            }

            return report

        except Exception as e:
            logger.error("Gemma Match Report failed", error=str(e))
            return {
                "score": 0,
                "synthesis": "Analysis unavailable at this time.",
                "gap": "N/A",
                "action_plan": "N/A",
                "thinking_process": ""
            }

    def _extract_value(self, text: str, label: str) -> str:
        """Helper to extract labeled values from LLM response"""
        if label not in text:
            return "N/A"
        try:
            start = text.find(label) + len(label)
            # Find next label or end of string
            next_labels = ["MATCH_SCORE:", "SYNTHESIS:", "THE_GAP:", "ACTION_PLAN:"]
            end = len(text)
            for nl in next_labels:
                pos = text.find(nl, start)
                if pos != -1 and pos < end:
                    end = pos
            return text[start:end].strip()
        except:
            return "N/A"

# Global instance
gemma_matching_service = GemmaMatchingService()
