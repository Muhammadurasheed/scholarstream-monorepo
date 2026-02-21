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
from google.generativeai.types import FunctionDeclaration, Tool, HarmCategory, HarmBlockThreshold
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
        # Try initializing Vertex AI first (Enterprise/Production path)
        self.use_vertex = False
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel, Tool as VertexTool, FunctionDeclaration as VertexFunctionDeclaration
            import google.auth
            from google.auth.exceptions import DefaultCredentialsError

            # STRICT CHECK: Only use Vertex if we have actual Google Cloud credentials (ADC)
            try:
                credentials, project = google.auth.default()
                vertexai.init(project=project, location="us-central1")
                self.use_vertex = True
                logger.info("Vertex AI initialized for Chat", mode="enterprise_adc")
            except DefaultCredentialsError:
                logger.warning("No Google Cloud ADC found for Chat. Vertex AI SDK skipped.")
                raise Exception("No ADC")

        except Exception:
            logger.warning("Vertex AI initialization failed for Chat. Falling back to API Key.")
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

        if self.use_vertex:
            from vertexai.generative_models import GenerativeModel, Tool as VertexTool, FunctionDeclaration as VertexFunctionDeclaration
            
            # Re-define tools for Vertex AI SDK (it uses slightly different class structure)
            vertex_tools = [
                VertexTool(
                    function_declarations=[
                        VertexFunctionDeclaration(
                            name="search_database",
                            description="Search the local database for scholarships, hackathons, and bounties. Use this for specific types or general searches.",
                            parameters={
                                "type": "object",
                                "properties": {
                                    "type": {"type": "string", "description": "Type of opportunity: 'scholarship', 'hackathon', 'bounty', 'grant', or 'any'"},
                                    "min_amount": {"type": "integer", "description": "Minimum amount in USD (optional)"},
                                    "limit": {"type": "integer", "description": "Max results to return (default 20)"}
                                },
                            }
                        ),
                        VertexFunctionDeclaration(
                            name="vector_search",
                            description="Semantic search to find matches by meaning (e.g. 'Lagos hackathon', 'freshman funding'). Use this for keyword-rich requests.",
                            parameters={
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string", "description": "The search query"},
                                    "limit": {"type": "integer", "description": "Max results to return (default 20)"}
                                },
                                "required": ["query"]
                            }
                        ),
                        VertexFunctionDeclaration(
                            name="dispatch_scout",
                            description="Fire autonomous web crawlers (Sentinel/Cortex) to find FRESH online opportunities. Use this if the DB results seem thin or user wants something now.",
                            parameters={
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string", "description": "Crawler search query (e.g. 'hackathons Feb 2026')"}
                                },
                                "required": ["query"]
                            }
                        ),
                        VertexFunctionDeclaration(
                            name="get_user_info",
                            description="Get the current user's profile details (school, major, interests).",
                            parameters={"type": "object", "properties": {}}
                        )
                    ]
                )
            ]
            
        # Define Safety Settings (Disable strict blocking for tool reasoning)
        vertex_safety = {}
        standard_safety = {}
        
        if self.use_vertex:
            from vertexai.generative_models import HarmCategory as VHC, HarmBlockThreshold as VHB
            vertex_safety = {
                VHC.HARM_CATEGORY_HARASSMENT: VHB.BLOCK_NONE,
                VHC.HARM_CATEGORY_HATE_SPEECH: VHB.BLOCK_NONE,
                VHC.HARM_CATEGORY_SEXUALLY_EXPLICIT: VHB.BLOCK_NONE,
                VHC.HARM_CATEGORY_DANGEROUS_CONTENT: VHB.BLOCK_NONE,
            }
        
        standard_safety = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        # DYNAMIC SYSTEM INSTRUCTION with CURRENT DATE
        current_date = datetime.now().strftime("%B %d, %Y")
        system_instruction = f"""You are ScholarStream AI, a world-class opportunity advisor and empathetic mentor.
Current Date: {current_date}

You have access to powerful tools to find scholarships, hackathons, and bounties for students.

Tone: Professional, warm, globally inclusive, and highly empathetic. Think "Google Principal Engineering meets human-centric design."

CORE ADVISOR RULES (GLOBAL STANDARDS):
1. **Empathy First**: Acknowledge user stress, tight deadlines, or financial concerns with genuine, professional warmth before acting. Keep it neutral and globally appealable.
2. **Eager Discovery (Smart Rendering)**: 
   - ALWAYS call `search_database` or `vector_search` FIRST for immediate results. 
   - Present these results as "Found in our repository".
   - SIMULTANEOUSLY call `dispatch_scout` for any urgent or specific requests to hunt for fresh leads in the background.
3. **Temporal Awareness**: You are aware that it is currently {current_date}. Use this for deadline calculations.
4. **Transparency**: Explain why you are using scouts (e.g., "to ensure you don't miss any brand-new 2026 funding opportunities").

Output strictly natural language in final response. Avoid specific religious or localized jargon to maintain a broad, inclusive appeal."""

        if self.use_vertex:
            self.model = GenerativeModel(
                model_name=settings.gemini_model,
                tools=vertex_tools,
                system_instruction=system_instruction,
                safety_settings=vertex_safety
            )
        else:
            self.model = genai.GenerativeModel(
                model_name=settings.gemini_model,
                tools=self.tools,
                system_instruction=system_instruction,
                safety_settings=standard_safety
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
        def json_serial(obj):
            """JSON serializer for objects not serializable by default json code"""
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            return str(obj)

        # Contextual metadata to keep the model grounded (DYNAMIC & GLOBAL-GRADE)
        current_date = datetime.now().strftime("%B %d, %Y")
        profile = context.get('user_profile', {})
        context_str = f"""
[SYSTEM CONTEXT]
Current Date: {current_date}
User Profile: {json.dumps(profile, default=json_serial)}
Target Audience: Global, inclusive, professional students.
Eager Discovery Plan: 
- Use `search_database` IMMEDIATELY to find existing legacy opportunities.
- Trigger `dispatch_scout` aggressively for fresh 2026 events.
- If the user has a specific deadline (e.g. Feb 25th), prioritize 'Rapid Funding' and 'Emergency Grants'.
- Synthesize advice that acknowledges the user's specific urgency and constraints profile.
[/SYSTEM CONTEXT]
"""

        try:
            # Initialize thinking process early to avoid UnboundLocalError
            thinking_process = ["🧠 **Analyzing request with FAANG-grade precision...**"]
            
            # Initialize conversation with history
            # For Vertex/Gemini dual support, we avoid enable_automatic_function_calling=True
            # and use our manual ReAct loop below.
            if self.use_vertex:
                # Vertex SDK start_chat is different
                chat = self.model.start_chat()
            else:
                chat = self.model.start_chat(enable_automatic_function_calling=False)
            
            # Start the ReAct turn
            response = await chat.send_message_async(message + context_str)

            tool_outputs = {}
            final_text = ""
            
            # Loop for multi-turn tool use (max 5 turns to prevent infinite loops)
            for i in range(5):
                fn = None # Initialize fn at the start of each turn
                # Iterate through ALL parts to find a function call
                # Gemini 2.0 often outputs text reasoning BEFORE the function call
                
                # Check ALL parts for function call
                # Vertex and Standard SDKs have slightly different structures, handled here
                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        fn = part.function_call
                        # Found a function call!
                        func_name = fn.name
                        # Vertex args are already dict-like, standard SDK needs dict()
                        func_args = dict(fn.args)
                        
                        # Use context-rich logging
                        target_hint = func_args.get('type') or func_args.get('query') or 'your situation'
                        if func_name == 'search_database':
                            thinking_process.append(f"🧠 **Reasoning:** I'm scanning our internal records for any befitting {target_hint} that match your profile.")
                        elif func_name == 'dispatch_scout':
                            thinking_process.append(f"🛠️ **Action:** Dispatched autonomous agents (Sentinel) to hunt for FRESH {target_hint} online.")
                        else:
                            thinking_process.append(f"🧠 **Thought:** Seeking clarity on '{target_hint}' via `{func_name}`...")
                        
                        logger.info("Agent invoking tool", tool=func_name, args=func_args)
                        break 
                    
                    # If it's text, log it as reasoning
                    if part.text:
                        thinking_process.append(f"🧠 **Thought:** {part.text}")

                # If we found a function call (fn is set), execute it
                if fn:
                    # func_name and func_args are already set in loop above
                    
                    # Execute tool provided in self.tools_map
                    if func_name in self.tools_map:
                        try:
                            # Execute async tool
                            result = await self.tools_map[func_name](user_id, **func_args)
                            
                            # Store result
                            tool_outputs[func_name] = result
                            
                            # Log observation with specificity
                            if isinstance(result, list) and len(result) > 0:
                                sample_types = list(set([o.get('type','items') for o in result[:3]]))
                                types_str = f"{', '.join(sample_types)}"
                                thinking_process.append(f"🔎 **Observation:** Found {len(result)} {types_str} results that look promising.")
                            else:
                                thinking_process.append(f"🔎 **Observation:** No direct matches found in this step. Adjusting my search...")
                            
                            # Feed result back to model
                            if self.use_vertex:
                                from vertexai.generative_models import Content, Part
                                # Vertex requires explicit history + tool response
                                # Simplified for now: we restart chat with history
                                # Note: Vertex SDK handles history in ChatSession better, but for manual loop we rebuild
                                response = await self.model.start_chat(history=[
                                    Content(role="user", parts=[Part.from_text(message + context_str)]),
                                    Content(role="model", parts=[part])
                                ]).send_message_async(
                                    Part.from_function_response(
                                        name=func_name,
                                        response={'result': result}
                                    )
                                )
                            else:
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
                            
                        except Exception as e:
                            logger.error("Tool execution failed", tool=func_name, error=str(e))
                            thinking_process.append(f"⚠️ **Error:** Tool `{func_name}` failed: {str(e)}")
                            break
                    else:
                        break # Unknown tool
                else:
                    # Model produced text response - we are done
                    final_text = part.text
                    thinking_process.append("✅ **Plan:** Synthesizing final response.")
                    break

            # IMPORTANT: Re-invoke the model once more if we only have tool results but no text
            # This allows the model to summarize the found opportunities empathetically.
            if not final_text and tool_outputs:
                thinking_process.append("✅ **Synthesis:** Finalizing my advice based on what I found...")
                
                # Construct a synthetic turn to get the model's final word
                summary_prompt = "I have gathered the information from my tools. Summarize your findings empathetically, acknowledging the user's specific constraints (deadlines, financial need) if mentioned. Don't mention tool names."
                
                if self.use_vertex:
                    # In Vertex manual loop, we send one last message
                    response = await self.model.start_chat(history=[
                        Content(role="user", parts=[Part.from_text(message + context_str)]),
                        Content(role="model", parts=[part])
                    ]).send_message_async(summary_prompt)
                    final_text = response.candidates[0].content.parts[0].text
                else:
                    # Standard SDK
                    from vertexai.generative_models import Part as VertexPart # Need for type consistency if mixed
                    response = await gemini_rate_limiter.execute(
                        self._raw_gemini_reply_with_text,
                        message=summary_prompt,
                        previous_history=[
                             {"role": "user", "parts": [message + context_str]},
                             {"role": "model", "parts": [part]}
                        ]
                    )
                    final_text = response.text

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
            thinking_process.append("📊 **Analysis:** Ranking and scoring opportunities for you...")
            ranked_opps = self._rank_opportunities(all_opportunities, profile)

            return {
                'message': final_text,
                'thinking_process': "\n\n".join(thinking_process),
                'opportunities': ranked_opps[:12],
                'suggestions': self._generate_suggestions(final_text, ranked_opps),
                'actions': self._generate_actions(ranked_opps)
            }

        except Exception as e:
            logger.error("ReAct Agent failed", error=str(e))
            import traceback
            traceback.print_exc()
            
            # Preserve the thinking process so the user sees what happened
            error_msg = f"⚠️ **Agent Error:** {str(e)}"
            if "429" in str(e):
                error_msg = "⚠️ **High Traffic:** I'm having trouble thinking clearly due to high load. Please try again in a minute."
            
            thinking_process.append(error_msg)
            
            return {
                'message': "I apologize, but I encountered an error while processing your request. Please check the logs above for details.",
                'opportunities': [],
                'thinking_process': "\n".join(thinking_process),
                'suggestions': [],
                'actions': []
            }

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TOOLS IMPLEMENTATION
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        return filtered[:limit]

    async def _tool_search_database(self, user_id: str, type: str = "any", min_amount: int = 0, limit: int = 20):
        """Tool: Search local database with filters"""
        # Ensure numeric types are actually integers/numbers (LLMs sometimes pass strings)
        try:
             limit = int(limit)
             min_amount = int(min_amount)
        except (ValueError, TypeError):
             limit = 20
             min_amount = 0

        start = datetime.now()
        now_str = start.strftime("%Y-%m-%d")
        opps = await db.get_all_scholarships()
        
        filtered = []
        for o in opps:
            try:
                # Convert Pydantic model to dict for safe access
                o_dict = o.model_dump() if hasattr(o, 'model_dump') else o.dict()
            except Exception:
                # Fallback if it's already a dict or something else
                o_dict = dict(o) if isinstance(o, dict) else {}

            # 1. STRICT DEADLINE GUARD (Principal Engineering Standard)
            # Filter out any opportunity where the deadline has passed
            deadline = o_dict.get('deadline')
            if deadline and deadline < now_str:
                continue

            # 2. Type filtering logic
            if type != "any" and type.lower() not in self._infer_type(o_dict):
                continue
            
            # 3. Filter by amount
            amt = o_dict.get('amount') or 0
            if amt < min_amount:
                continue
                
            filtered.append(o_dict)
            
        return filtered[:limit]

    async def _tool_vector_search(self, user_id: str, query: str, limit: int = 20):
        """Tool: Search by semantic meaning"""
        try:
            limit = int(limit)
        except (ValueError, TypeError):
            limit = 20

        try:
            from app.services.vectorization_service import vectorization_service
            vec = await vectorization_service.vectorize_query(query)
            if not vec: return []
            
            results = await db.semantic_search(vec, limit=limit * 2) # Get more to allow for filtering
            
            now_str = datetime.now().strftime("%Y-%m-%d")
            filtered = []
            for r in results:
                r_dict = r.dict()
                deadline = r_dict.get('deadline')
                if deadline and deadline < now_str:
                    continue
                filtered.append(r_dict)
                if len(filtered) >= limit:
                    break
            return filtered
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
        if self.use_vertex:
             # Vertex SDK GenerativeModel has generate_content_async too
             # But the 'tools' were already set at init for Vertex
             return await self.model.generate_content_async(prompt)
        else:
            # Standard SDK
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

    async def _raw_gemini_reply_with_text(self, message, previous_history):
        """Standard SDK turn for text-only summary"""
        model = genai.GenerativeModel(settings.gemini_model, tools=self.tools)
        chat = model.start_chat(history=previous_history)
        return await chat.send_message_async(message)

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

        if any(kw in combined for kw in ['hackathon', 'hack', 'buildathon', 'codeathon', 'ideathon', 'builder']):
            return 'hackathon'
        elif any(kw in combined for kw in ['bounty', 'bug bounty', 'vulnerability', 'testnet', 'auditing']):
            return 'bounty'
        elif any(kw in combined for kw in ['competition', 'contest', 'challenge', 'olympiad', 'tournament', 'quiz']):
            return 'competition'
        elif any(kw in combined for kw in ['grant', 'funding', 'seed', 'investment', 'acceleration', 'equity-free']):
            return 'grant'
        elif any(kw in combined for kw in ['internship', 'intern', 'fellowship', 'graduate program', 'trainee', 'apprentice']):
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
        """
        Multidimensional Diversity Interleaving (Google-grade logic).
        Balances by both 'Type' and 'Platform/Source'.
        """
        if len(sorted_results) <= 4: # Very low results - don't interleave
            return sorted_results

        final = []
        used_ids = set()

        def get_platform(opp):
            url = (opp.get('source_url') or "").lower()
            if 'dorahacks' in url: return 'dorahacks'
            if 'devpost' in url: return 'devpost'
            if 'mlh.io' in url: return 'mlh'
            if 'devfolio' in url: return 'devfolio'
            if 'hackquest' in url: return 'hackquest'
            if 'lablab' in url: return 'lablab'
            if 'scholarships.com' in url or 'fastweb' in url: return 'scholarship_hub'
            return 'other'

        # Phase 1: Top 4 by pure relevance/score (High-confidence anchors)
        for item in sorted_results[:4]:
            final.append(item)
            used_ids.add(item['id'])

        # Phase 2: Interleave remaining slots by Platform AND Type
        buckets: Dict[str, List[Dict]] = {}
        for item in sorted_results:
            if item['id'] in used_ids: continue
            
            platform = get_platform(item)
            opp_type = item.get('type', 'scholarship')
            
            # Create a combined diversity key
            comb_key = f"{platform}_{opp_type}"
            buckets.setdefault(comb_key, []).append(item)

        bucket_keys = list(buckets.keys())
        # Sort bucket keys by the highest score in each bucket to maintain some relevance
        bucket_keys.sort(key=lambda k: buckets[k][0].get('match_score', 0) if buckets[k] else 0, reverse=True)
        
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
            if len(final) >= target_count: break
            if item['id'] not in used_ids:
                final.append(item)
                used_ids.add(item['id'])

        return final

# Instantiate
chat_service = ReActChatService()

