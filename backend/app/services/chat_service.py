"""
ScholarStream AI Chat Service — V4: True ReAct Agent Architecture

Architecture:
  User Message
       │
       ▼
  ┌─────────────────────────────────┐
  │  Gemini Pro (as Reasoning Engine)│  ← "I need to check the DB first..."
  └─────────────────────────────────┘
       │
       ├── Calls Tool: search_database(query="scholarships for nursing")
       │     │
       │     ▼
       │   [Tool Output: 2 results found]
       │
       ▼
  ┌─────────────────────────────────┐
  │  Gemini Pro (Reasoning)         │  ← "Results are thin. I should search online."
  └─────────────────────────────────┘
       │
       ├── Calls Tool: dispatch_scout(query="nursing scholarships 2026 application")
       │     │
       │     ▼
       │   [Tool Output: Scouts dispatched]
       │
       ▼
  ┌─────────────────────────────────┐
  │  Gemini Pro (Response)          │  ← "I found a few in our database, and I've sent agents to find more..."
  └─────────────────────────────────┘

Design: Google-grade Agentic Workflow. The model decides the path.
"""

import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool
import json
import asyncio
from typing import Dict, Any, List, Optional
import structlog
from datetime import datetime, timedelta

from app.models import UserProfile, Scholarship
from app.database import db
from app.config import settings
from app.services.matching_service import matching_service
from app.services.personalization_engine import personalization_engine
from app.services.cortex.navigator import scout, sentinel
from app.utils.rate_limiter import gemini_rate_limiter

logger = structlog.get_logger()

class ReActChatService:
    """True AI Agent powered by Gemini Function Calling"""

    def __init__(self):
        if not settings.gemini_api_key:
            raise Exception("GEMINI_API_KEY not configured in settings")

        genai.configure(api_key=settings.gemini_api_key)
        
        # ── Define Tools ──
        self.tools_map = {
            'search_database': self._tool_search_database,
            'vector_search': self._tool_vector_search,
            'dispatch_scout': self._tool_dispatch_scout,
            'get_user_info': self._tool_get_user_info,
            'filter_opportunities': self._tool_filter_opportunities
        }

        self.tools = [
            Tool(
                function_declarations=[
                    FunctionDeclaration(
                        name="search_database",
                        description="Search the local database for scholarships, hackathons, and bounties using structured filters.",
                        parameters={
                            "type": "object",
                            "properties": {
                                "type": {"type": "string", "description": "Type of opportunity: 'scholarship', 'hackathon', 'bounty', 'grant', or 'any'"},
                                "min_amount": {"type": "integer", "description": "Minimum amount in USD (optional)"},
                                "limit": {"type": "integer", "description": "Max results to return (default 20)"}
                            },
                        }
                    ),
                    FunctionDeclaration(
                        name="vector_search",
                        description="Perform a semantic search to find opportunities by meaning/context (e.g. 'funding for female engineers')",
                        parameters={
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Natural language query string describing what to find"},
                                "limit": {"type": "integer", "description": "Max results to return (default 20)"}
                            },
                            "required": ["query"]
                        }
                    ),
                    FunctionDeclaration(
                        name="dispatch_scout",
                        description="Dispatch autonomous web crawlers to find FRESH opportunities online. Use this when database results are poor or user wants new data.",
                        parameters={
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Specific search query for the crawler (e.g. 'hackathons in Lagos 2026')"}
                            },
                            "required": ["query"]
                        }
                    ),
                    FunctionDeclaration(
                        name="get_user_info",
                        description="Get the current user's profile details (school, major, interests).",
                        parameters={"type": "object", "properties": {}}
                    )
                ]
            )
        ]

        # Initialize GenerativeModel with tools
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            tools=self.tools,
            system_instruction="""You are ScholarStream AI, a world-class opportunity advisor.
You have access to powerful tools to find scholarships, hackathons, and bounties for students.
Your goal is to be helpful, proactive, and empathetic.

RULES:
1. ALWAYS start by getting the user's info if you don't have it.
2. Check the database (`search_database` or `vector_search`) FIRST.
3. If database results are thin (<5) or irrelevant, OR if the request implies urgency/freshness, MUST call `dispatch_scout` to search the live web.
4. "Urgent", "Deadline", "Fast" = HIGH priority. Search for quick-turnaround opportunities.
5. Provide a helpful final response summarizing what you found and what agents you dispatched.
6. Be concise but warm. Use "Empathy Sandwich" for stressed users.

Output strictly natural language in the final response."""
        )

        logger.info("ReAct Chat Agent initialized", model=settings.gemini_model)

    async def chat(
        self,
        user_id: str,
        message: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute the ReAct loop (Reason -> Act -> Observe -> Response).
        """
        try:
            # Initialize conversation with history if we had it (skipping for this MVP, treating each req as fresh context)
            chat = self.model.start_chat(enable_automatic_function_calling=True)
            
            # Inject context into the user message invisibly
            profile = context.get('user_profile', {})
            context_str = f"\n[System Context: User ID: {user_id}, Name: {profile.get('name', 'Unknown')}, Major: {profile.get('major', 'Unknown')}]"
            
            # ── EXECUTE AGENT LOOP ──
            # With enable_automatic_function_calling=True, the SDK handles the loop!
            # It will call our local functions defined in _tool_* methods automatically.
            # BUT: The SDK expects the actual functions to be passed, not just declarations.
            # The current google-generativeai SDK's automatic calling features are limited.
            # We implemented a MANUAL loop below for full control and robustness.
            
            # 1. First turn: Send user message
            response = await gemini_rate_limiter.execute(
                self._raw_gemini_start_chat, 
                message + context_str,
                self.tools
            )

            tool_outputs = {}
            final_text = ""
            thinking_process = ["🧠 **Analyzing request...**"]
            
            # Loop for multi-turn tool use (max 5 turns to prevent infinite loops)
            for _ in range(5):
                part = response.candidates[0].content.parts[0]
                
                # Check if model wants to call a function
                if fn := part.function_call:
                    func_name = fn.name
                    func_args = dict(fn.args)
                    
                    thinking_process.append(f"🛠️ **Agent Action:** Calling `{func_name}`...")
                    logger.info("Agent invoking tool", tool=func_name, args=func_args)
                    
                    # Execute tool provided in self.tools_map
                    if func_name in self.tools_map:
                        try:
                            # Execute async tool
                            result = await self.tools_map[func_name](user_id, **func_args)
                            
                            # Store result
                            tool_outputs[func_name] = result
                            
                            # Feed result back to model
                            response = await gemini_rate_limiter.execute(
                                self._raw_gemini_reply_with_function,
                                chat_session=None, # We are doing manual stateless turns for control
                                function_name=func_name,
                                function_response=result,
                                previous_history=[
                                    {"role": "user", "parts": [message + context_str]},
                                    {"role": "model", "parts": [part]}
                                ]
                            )
                            
                            thinking_process.append(f"  → Result: Found {len(result) if isinstance(result, list) else 'info'}")
                        except Exception as e:
                            logger.error("Tool execution failed", tool=func_name, error=str(e))
                            break
                    else:
                        break # Unknown tool
                else:
                    # Model produced text response - we are done
                    final_text = part.text
                    break

            # If we exited loop without text (e.g. tool loop limit), force a text generation
            if not final_text and tool_outputs:
                 final_text = "I've gathered the information you asked for. Please check the results below."

            # Persist chat
            await db.save_chat_message(user_id, "user", message)
            await db.save_chat_message(user_id, "assistant", final_text)

            # Collect opportunities from tool outputs
            all_opportunities = []
            if 'search_database' in tool_outputs:
                all_opportunities.extend(tool_outputs['search_database'])
            if 'vector_search' in tool_outputs:
                # Deduplicate
                pkg_ids = {o['id'] for o in all_opportunities}
                for o in tool_outputs['vector_search']:
                    if o['id'] not in pkg_ids:
                        all_opportunities.append(o)
            
            # Personalize/Score them
            ranked_opps = self._rank_opportunities(all_opportunities, profile)

            return {
                'message': final_text,
                'thinking_process': "\n".join(thinking_process),
                'opportunities': ranked_opps[:12],
                'suggestions': self._generate_suggestions(final_text, ranked_opps),
                'actions': self._generate_actions(ranked_opps)
            }

        except Exception as e:
            logger.error("ReAct Agent failed", error=str(e))
            import traceback
            traceback.print_exc()
            return {
                'message': "I'm having a bit of trouble connecting to my tools right now. I've noted your request and will try to process it shortly.",
                'opportunities': [],
                'thinking_process': "⚠️ **Agent Error:** Connection interrupted during reasoning step."
            }

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TOOLS IMPLEMENTATION
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def _tool_search_database(self, user_id: str, type: str = "any", min_amount: int = 0, limit: int = 20):
        """Tool: Search local database with filters"""
        start = datetime.now()
        opps = await db.get_all_scholarships()
        
        filtered = []
        for o in opps:
            # Basic type filtering logic...
            if type != "any" and type.lower() not in self._infer_type(o):
                continue
            if o.amount and o.amount < min_amount:
                continue
            filtered.append(o.dict())
            
        return filtered[:limit]

    async def _tool_vector_search(self, user_id: str, query: str, limit: int = 20):
        """Tool: Search by semantic meaning"""
        try:
            from app.services.vectorization_service import vectorization_service
            vec = await vectorization_service.vectorize_query(query)
            if not vec: return []
            
            results = await db.semantic_search(vec, limit=limit)
            return [r.dict() for r in results]
        except Exception as e:
            logger.error("Vector search tool failed", error=str(e))
            return []

    async def _tool_dispatch_scout(self, user_id: str, query: str):
        """Tool: Dispatch live crawler"""
        # Fire and forget - don't wait for crawl to finish
        asyncio.create_task(scout.execute_mission(query))
        return {"status": "scouts_dispatched", "message": f"Agents searching for '{query}'"}

    async def _tool_get_user_info(self, user_id: str):
        """Tool: Get user profile"""
        profile = await db.get_user_profile(user_id)
        return profile or {}

    async def _tool_filter_opportunities(self, user_id: str):
        return []

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # HELPERS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def _raw_gemini_start_chat(self, prompt, tools):
        """Wrapped call for start of chat"""
        model = genai.GenerativeModel(settings.gemini_model, tools=tools)
        return await model.generate_content_async(prompt)

    async def _raw_gemini_reply_with_function(self, chat_session, function_name, function_response, previous_history):
        """Wrapped call for sending tool outputs back"""
        # Construct the response part
        from google.ai.generativelanguage_v1beta.types import content
        
        # We need to manually reconstruct the chat turn structure for the stateless API usage
        # This is complex in the raw API, simplification:
        # We re-instantiate a chat with history and send the function response
        
        tool_response = content.Part(
            function_response=content.FunctionResponse(
                name=function_name,
                response={'result': function_response}
            )
        )
        
        model = genai.GenerativeModel(settings.gemini_model, tools=self.tools)
        chat = model.start_chat(history=previous_history)
        return await chat.send_message_async(tool_response)

    def _rank_opportunities(self, opps: List[Dict], profile: Dict) -> List[Dict[str, Any]]:
        """Score, rank, and format opportunities."""
        from app.services.personalization_engine import personalization_engine
        
        user_profile_obj = None
        try:
            user_profile_obj = UserProfile(**profile) if profile else None
        except Exception:
            pass

        results = []
        for opp in opps:
            opp_dict = opp if isinstance(opp, dict) else (opp.model_dump() if hasattr(opp, 'model_dump') else opp.dict() if hasattr(opp, 'dict') else {})
            
            # Fresh match score
            score = 50
            if user_profile_obj:
                try:
                    score = personalization_engine.calculate_personalized_score(opp_dict, user_profile_obj)
                except Exception:
                    score = opp_dict.get('match_score', 50)
            else:
                score = opp_dict.get('match_score', 50)

            results.append({
                'id': opp_dict.get('id'),
                'name': opp_dict.get('name'),
                'organization': opp_dict.get('organization'),
                'amount': opp_dict.get('amount'),
                'amount_display': opp_dict.get('amount_display'),
                'deadline': opp_dict.get('deadline'),
                'type': self._infer_type(opp_dict),
                'match_score': int(round(score)),
                'source_url': opp_dict.get('source_url'),
                'tags': opp_dict.get('tags'),
                'description': opp_dict.get('description'),
                'location_eligibility': self._get_location_string(opp_dict),
                'priority_level': opp_dict.get('priority_level')
            })

        # Sort by score, then interleave for diversity
        results.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        return self._interleave_for_diversity(results, target_count=12)

    def _infer_type(self, opp) -> str:
        """Infer opportunity type from tags/description."""
        tags_str = ' '.join(opp.get('tags', []) or []).lower()
        desc_str = (opp.get('description') or '').lower()
        name_str = (opp.get('name') or '').lower()
        combined = f"{tags_str} {desc_str} {name_str}"

        if any(kw in combined for kw in ['hackathon', 'hack', 'buildathon', 'codeathon']):
            return 'hackathon'
        elif any(kw in combined for kw in ['bounty', 'bug bounty', 'vulnerability']):
            return 'bounty'
        elif any(kw in combined for kw in ['competition', 'contest', 'challenge', 'olympiad']):
            return 'competition'
        elif any(kw in combined for kw in ['grant', 'funding', 'seed']):
            return 'grant'
        elif any(kw in combined for kw in ['internship', 'intern', 'fellowship']):
            return 'internship'
        return 'scholarship'

    def _get_location_string(self, opp) -> str:
        """Human-readable location eligibility."""
        eligibility = opp.get('eligibility', {})
        if hasattr(eligibility, 'dict'):
            eligibility = eligibility.dict()
        elif hasattr(eligibility, 'model_dump'):
            eligibility = eligibility.model_dump()
        
        # Handle if it's already a dict or None
        if not eligibility:
            return "Open / International"
            
        states = eligibility.get('states') or []
        citizenship = eligibility.get('citizenship')

        if states:
            return f"Residents of {', '.join(states)}"
        if citizenship and citizenship.lower() != 'any':
            return f"Citizens of {citizenship}"
        return "Open / International"

    def _generate_suggestions(self, text: str, opps: List[Dict]) -> List[str]:
        """Generate smart follow-up suggestions."""
        base = ["Find more opportunities", "Filter by amount", "Show deadlines"]
        if "scholarship" in text.lower():
            base.insert(0, "How do I apply?")
        if opps and any(o['type'] == 'hackathon' for o in opps[:3]):
            base.insert(1, "Find teammates for hackathons")
        return base[:3]

    def _generate_actions(self, opportunities: List[Dict]) -> List[Dict[str, Any]]:
        """Generate context-appropriate actions."""
        actions = []

        if opportunities:
            actions.append({
                'type': 'navigate',
                'label': '🎯 View Top Match',
                'data': {'path': f"/opportunity/{opportunities[0]['id']}"}
            })
            if len(opportunities) >= 2:
                actions.append({
                    'type': 'save',
                    'label': '💾 Save All Matches',
                    'data': {'opportunity_ids': [o['id'] for o in opportunities[:5]]}
                })

        return actions
    
    def _interleave_for_diversity(self, sorted_results: List[Dict], target_count: int = 12) -> List[Dict]:
        """Relevance-first diversity interleaving."""
        if len(sorted_results) <= target_count:
            return sorted_results

        final = []
        used_ids = set()

        # Phase 1: Top 6 by pure relevance
        for item in sorted_results[:6]:
            final.append(item)
            used_ids.add(item['id'])

        # Phase 2: Round-robin by type
        buckets: Dict[str, List[Dict]] = {}
        for item in sorted_results:
            if item['id'] in used_ids:
                continue
            t = item.get('type', 'scholarship')
            buckets.setdefault(t, []).append(item)

        bucket_keys = list(buckets.keys())
        idx = 0
        while len(final) < target_count and bucket_keys:
            key = bucket_keys[idx % len(bucket_keys)]
            if buckets[key]:
                item = buckets[key].pop(0)
                final.append(item)
                used_ids.add(item['id'])
            else:
                bucket_keys.remove(key)
                if not bucket_keys:
                    break
            idx += 1

        # Backfill if short
        for item in sorted_results:
            if len(final) >= target_count:
                break
            if item['id'] not in used_ids:
                final.append(item)
                used_ids.add(item['id'])

        return final

# Instantiate
chat_service = ReActChatService()

