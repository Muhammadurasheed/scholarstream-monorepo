"""
Gemma 4 AI Service (Native Implementation)
Hosts the Scholar-Einstein agent logic using Gemma 4 via Vertex AI Maas.
"""
import os
import httpx
import json
import structlog
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import google.auth
import google.auth.transport.requests

from app.config import settings
from app.utils.rate_limiter import gemini_rate_limiter
from app.models import (
    ScrapedScholarship,
    UserProfile,
    AIEnrichmentResponse,
    ScholarshipEligibility,
    ScholarshipRequirements
)

logger = structlog.get_logger()

class GemmaAIService:
    """
    Native Gemma 4 integration for ScholarStream.
    Uses Thinking Mode for deep reasoning and System Prompts for personality.
    """
    
    def __init__(self):
        self.project_id = settings.firebase_project_id or "scholarstream-gemma4good"
        self.region = "global"
        self.endpoint = f"https://aiplatform.googleapis.com/v1/projects/{self.project_id}/locations/{self.region}/endpoints/openapi/chat/completions"
        self.model_id = "google/gemma-4-26b-a4b-it-maas"
        
        # Tool Map for ReAct execution
        self.tools = []
        
        # Initialize Google Credentials (ADC)
        try:
            self.creds, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
            logger.info("Gemma AI initialized with Cloud ADC", project_id=self.project_id)
        except Exception as e:
            logger.error("Failed to initialize Gemma AI credentials", error=str(e))
            self.creds = None

    async def get_access_token(self) -> str:
        """Refresh and return the GCP access token"""
        if not self.creds:
            raise Exception("GCP Credentials not initialized")
            
        if not self.creds.valid:
            auth_req = google.auth.transport.requests.Request()
            self.creds.refresh(auth_req)
        
        return self.creds.token

    async def generate_content_async(
        self, 
        prompt: str, 
        system_instruction: Optional[str] = None,
        enable_thinking: bool = True,
        tools: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Execute a chat completion against Gemma 4 via Vertex AI Maas using API Key.
        """
        api_key = settings.gemini_api_key
        url = f"{self.endpoint}?key={api_key}"
        
        async def _raw_call() -> Dict:
            headers = {
                "Content-Type": "application/json"
            }
            
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model_id,
                "messages": messages,
                "stream": False,
                "max_tokens": 8192,
                "chat_template_kwargs": {
                    "enable_thinking": enable_thinking
                }
            }
            
            if tools:
                payload["tools"] = [{"type": "function", "function": t} for t in tools]
                payload["tool_choice"] = "auto"
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()

        return await gemini_rate_limiter.execute(_raw_call)

    async def analyze_query_intent(self, user_query: str) -> Dict[str, Any]:
        """Deep intent analysis using Gemma's thinking mode"""
        system_prompt = "You are the Scholar-Einstein Intent Analyzer. You detect urgency and hidden student needs."
        
        prompt = f"""
        Analyze this student query: "{user_query}"
        
        TASK:
        1. Detect URGENCY (True/False).
        2. Identify target entities (Location, Degree, Field).
        3. Optimize search terms.

        Return JSON only:
        {{
            "is_urgent": bool,
            "suggested_filters": {{ "priority_level": "URGENT" or "MEDIUM" }},
            "vector_search_query": "optimized string"
        }}
        """
        
        try:
            response_json = await self.generate_content_async(prompt, system_instruction=system_prompt)
            content = response_json["choices"][0]["message"]["content"]
            return self._parse_json_safe(content)
        except Exception as e:
            logger.error("Gemma intent analysis failed", error=str(e))
            return {"is_urgent": False, "filters": {}, "vector_query": user_query}

    def _parse_json_safe(self, text: str) -> Dict:
        """Helper to clean and parse JSON from Gemma's response"""
        text = text.strip()
        # Handle thinking block if present (Gemma might return <thought>...</thought> if not stripped by Maas)
        if "</thought>" in text:
            text = text.split("</thought>")[-1].strip()
            
        if text.startswith('```json'): text = text[7:]
        if text.startswith('```'): text = text[3:]
        if text.endswith('```'): text = text[:-3]
        
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            # Last resort: try to find the first { and last }
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                return json.loads(text[start:end+1])
            raise

# Global Gemma service instance
gemma_service = GemmaAIService()
