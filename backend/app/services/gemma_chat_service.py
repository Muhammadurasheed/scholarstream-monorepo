"""
Gemma 4 ReAct Agent — V1: Semantic Reasoning & Autonomous Tool Execution.
Native implementation for Gemma 4 via Vertex AI Maas.
"""
import json
import asyncio
from typing import Dict, Any, List, Optional
import structlog
from datetime import datetime

from app.models import UserProfile
from app.database import db
from app.config import settings
from app.services.gemma_service import gemma_service
from app.services.cortex.navigator import scout

logger = structlog.get_logger()

class GemmaReActChatService:
    """
    Native Gemma 4 Agent.
    Implements a manual ReAct loop: Reason -> Tool Call -> Observation -> Final Answer.
    Uses Gemma 4's Thinking Mode for internal monologue.
    """

    def __init__(self):
        # Define tools for the agent (OpenAI-style schema)
        self.tool_definitions = [
            {
                "name": "search_database",
                "description": "Search for scholarships and hackathons in the local database using filters.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["scholarship", "hackathon", "bounty", "any"]},
                        "min_amount": {"type": "integer"}
                    }
                }
            },
            {
                "name": "vector_search",
                "description": "Search by meaning (e.g. 'coding for girls').",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "dispatch_scout",
                "description": "Search the live web for fresh opportunities.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"}
                    },
                    "required": ["query"]
                }
            }
        ]
        
        self.tools_map = {
            'search_database': self._tool_search_database,
            'vector_search': self._tool_vector_search,
            'dispatch_scout': self._tool_dispatch_scout
        }

    async def chat(self, user_id: str, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Manual ReAct loop for Gemma 4"""
        current_date = datetime.now().strftime("%B %d, %Y")
        profile = context.get('user_profile', {})
        
        system_instruction = f"""You are the Scholar-Einstein AI Agent, powered by Gemma 4.
Current Date: {current_date}
User Profile: {json.dumps(profile)}

Your goal is to find scholarships and hackathons. Use tools whenever possible to get real data.
Be empathetic, professional, and precise."""

        thinking_process = ["🧠 Analyzing request with Gemma 4 Reasoning..."]
        conversation_history = [{"role": "user", "content": message}]
        
        final_text = ""
        
        try:
            # ReAct Loop (Max 3 turns for performance)
            for turn in range(3):
                response_json = await gemma_service.generate_content_async(
                    prompt=message, 
                    system_instruction=system_instruction,
                    tools=self.tool_definitions
                )
                
                message_data = response_json["choices"][0]["message"]
                
                # Check for Tool Calls
                tool_calls = message_data.get("tool_calls")
                if tool_calls:
                    for tc in tool_calls:
                        fn_name = tc["function"]["name"]
                        fn_args = json.loads(tc["function"]["arguments"])
                        
                        thinking_process.append(f"🛠️ Executing {fn_name}...")
                        
                        # Execute Tool
                        if fn_name in self.tools_map:
                            tool_result = await self.tools_map[fn_name](user_id, **fn_args)
                            thinking_process.append(f"✅ Found {len(tool_result) if isinstance(tool_result, list) else 1} results.")
                            
                            # Feed result back to model (this would be turn 2)
                            # For simplicity in this version, we append to the message and continue
                            message += f"\n[Tool Output {fn_name}]: {json.dumps(tool_result)}"
                        else:
                            thinking_process.append(f"⚠️ Tool {fn_name} not found.")
                else:
                    # No tool calls, this is the final answer
                    final_text = message_data.get("content", "")
                    break
            
            # If we reached the end without a final answer, generate one last summary
            if not final_text:
                summary_resp = await gemma_service.generate_content_async(
                    prompt=f"Summarize the findings for the user based on our internal work: {message}",
                    system_instruction=system_instruction,
                    enable_thinking=False
                )
                final_text = summary_resp["choices"][0]["message"]["content"]

            return {
                "text": final_text,
                "thinking_process": thinking_process,
                "agent_status": "complete",
                "engine": "Gemma 4 Native"
            }

        except Exception as e:
            logger.error("Gemma Chat Loop failed", error=str(e))
            return {
                "text": "I encountered an error while processing your request with Gemma 4. Please try again.",
                "thinking_process": thinking_process + [f"❌ Error: {str(e)}"],
                "agent_status": "error"
            }

    # Tool Implementations (Mirroring ChatService)
    async def _tool_search_database(self, user_id, type="any", min_amount=0):
        # Actual implementation calls DB
        from app.database import db
        return await db.search_scholarships(query="", type=type, min_amount=min_amount, limit=5)

    async def _tool_vector_search(self, user_id, query, limit=5):
        from app.services.vectorization_service import vectorization_service
        vec = await vectorization_service.vectorize_query(query)
        return await db.semantic_search(vec, limit=limit)

    async def _tool_dispatch_scout(self, user_id, query):
        asyncio.create_task(scout.execute_mission(query))
        return {"status": "scouts_dispatched"}

# Instance
gemma_chat_service = GemmaReActChatService()
