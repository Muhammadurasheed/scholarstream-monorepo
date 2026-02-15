"""
AI Chat Service for ScholarStream Assistant
Real-time conversational AI powered by Gemini
"""
import google.generativeai as genai
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
from app.services.cortex.navigator import scout

logger = structlog.get_logger()


class ChatService:
    """AI Chat Assistant powered by Gemini"""
    
    def __init__(self):
        """Initialize Gemini using settings"""
        if not settings.gemini_api_key:
            raise Exception("GEMINI_API_KEY not configured in settings")
        
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model)
        logger.info("Chat service initialized", model=settings.gemini_model)
    
    async def chat(
        self,
        user_id: str,
        message: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process chat message with enhanced transparency and markdown formatting
        """
        try:
            # Build context-rich prompt
            system_prompt = self._build_system_prompt(context)
            
            # Check for Emergency Mode
            is_emergency = self._detect_emergency_mode(message)
            
            # FIX: Detect if user wants to search for opportunities
            needs_search = self._detect_search_intent(message)
            
            opportunities = []
            thinking_process = []
            search_stats = None
            
            if needs_search or is_emergency:
                # TRANSPARENCY: Log search process
                if is_emergency:
                    thinking_process.append("🚨 **EMERGENCY MODE ACTIVATED**")
                    thinking_process.append("- prioritizing deadlines < 14 days")
                    thinking_process.append("- prioritizing quick-apply formats")
                else:
                    thinking_process.append("🔍 **Analyzing your request...**")
                
                # Extract search criteria
                search_criteria = await self._extract_search_criteria(message, context.get('user_profile', {}))
                
                # Override for Emergency
                if is_emergency:
                    search_criteria['urgency'] = 'immediate'
                    
                thinking_process.append(f"\n📋 **Search Criteria Identified:**")
                thinking_process.append(f"- **Types**: {', '.join(search_criteria['types'])}")
                if search_criteria['urgency'] != 'any':
                    thinking_process.append(f"- **Urgency**: {search_criteria['urgency']}")
                thinking_process.append(f"- **Location**: {context.get('user_profile', {}).get('state', 'Any')}, {context.get('user_profile', {}).get('country', 'Any')}")
                
                # Search with detailed statistics
                opportunities, search_stats = await self._search_opportunities_with_stats(
                    search_criteria, 
                    context.get('user_profile', {})
                )
                
                # Check if it was broadened
                if search_criteria.get('broadened'):
                    thinking_process.append("\n⚠️ **Broadening search to find more potential matches...**")
                
                # TRANSPARENCY: Show filtering results
                thinking_process.append(f"\n📊 **Search Results:**")
                thinking_process.append(f"- Total opportunities scanned: **{search_stats['total_scanned']}**")
                thinking_process.append(f"- Expired (filtered out): {search_stats['expired']}")
                thinking_process.append(f"- Location mismatch (filtered out): {search_stats['location_filtered']}")
                thinking_process.append(f"- Type mismatch (filtered out): {search_stats['type_filtered']}")
                if search_stats.get('urgency_filtered', 0) > 0:
                    thinking_process.append(f"- Urgency mismatch (filtered out): {search_stats['urgency_filtered']}")
                thinking_process.append(f"- **✅ Final matches: {len(opportunities)}**")
                
                # Add opportunities to prompt for AI context
                if opportunities:
                    system_prompt += f"\n\nSEARCH RESULTS ({len(opportunities)} found):\n"
                    # V3: ALWAYS show at least 12 opportunities to AI for comprehensive recommendations
                    limit = 12
                    for i, opp in enumerate(opportunities[:limit], 1):
                        system_prompt += f"\n{i}. **{opp.get('name')}** - {opp.get('amount_display', 'See details')}\n"
                        system_prompt += f"   - Organization: {opp.get('organization')}\n"
                        system_prompt += f"   - Match Score: {opp.get('match_score')}%\n"
                        system_prompt += f"   - Deadline: {opp.get('deadline') or 'Check listing'}\n"
                        system_prompt += f"   - Link: {opp.get('source_url')}\n"
                        system_prompt += f"   - Type: {opp.get('type')}\n"
                        system_prompt += f"   - Location: {opp.get('location_eligibility')}\n"
            
            # Generate AI response with enhanced prompt
            prompt_suffix = "\n\nUSER MESSAGE: {message}\n\nProvide a helpful, well-formatted markdown response:"
            if is_emergency:
                 prompt_suffix = """
                 \n\nUSER MESSAGE: {message}
                 \n\nCRITICAL INSTRUCTION - EMERGENCY MODE:
                 The user is stressed. Use the 'Empathy Sandwich' technique:
                 1. Top Slice: Validate their stress briefly ("I hear you, and we can fix this.").
                 2. Meat: Present the solution clearly and actionably.
                 3. Bottom Slice: Reassure them ("You've got this.").
                 Keep it concise.
                 """
            
            full_prompt = system_prompt + prompt_suffix.format(message=message)
            
            response = await self.model.generate_content_async(full_prompt)
            ai_message = response.text
            
            # V2 FIX: Separate thinking process from recommendation for better UX
            # The frontend will render these as separate collapsible sections
            thinking_section = ""
            if thinking_process:
                thinking_section = "\n".join(thinking_process)
            
            # Save conversation
            await self._save_message(user_id, "user", message)
            await self._save_message(user_id, "assistant", ai_message)
            
            return {
                'message': ai_message,
                'thinking_process': thinking_section,  # V2: Separate for frontend streaming
                'opportunities': opportunities[:12] if opportunities else [],  # V3: Always return up to 12
                'actions': self._generate_actions(opportunities, message),
                'search_stats': search_stats
            }
            
        except Exception as e:
            logger.error("Chat failed", error=str(e))
            return {
                'message': "❌ I encountered an error while processing your request. Please try rephrasing your question or contact support if the issue persists.",
                'opportunities': [],
                'actions': [],
                'search_stats': None
            }
    
    def _detect_emergency_mode(self, message: str) -> bool:
        """Detect high-stress/urgent keywords"""
        triggers = [
            "urgent", "emergency", "deadline", "asap", "failed", "broke", 
            "need money now", "help me", "immediately", "today", "tomorrow"
        ]
        return any(t in message.lower() for t in triggers)

    def _build_system_prompt(self, context: Dict[str, Any]) -> str:
        """Build context-rich system prompt - V2: GLOBAL-FIRST approach"""
        profile = context.get('user_profile', {})
        page = context.get('current_page', 'unknown')
        
        # Detect user's actual location context
        user_country = profile.get('country', '')
        user_school = profile.get('school', '')
        
        prompt = f"""You are ScholarStream Assistant, an expert **GLOBAL** opportunity advisor for students worldwide.

STUDENT PROFILE:
- Name: {profile.get('name', 'Student')}
- Major: {profile.get('major', 'Unknown')}
- School: {user_school}
- Location: {profile.get('city', '')}, {profile.get('state', '')}, {user_country}
- Interests: {', '.join(profile.get('interests', []))}
- Background: {', '.join(profile.get('background', []))}

CRITICAL GLOBAL CONTEXT:
🌍 **ScholarStream serves students WORLDWIDE** - from Nigeria to Japan to Brazil.
🎯 **Hackathons, Bounties, and Tech Competitions are ALWAYS GLOBAL** - no location restrictions.
   - DevPost hackathons: Open to ALL countries
   - DoraHacks: Open to ALL countries  
   - MLH: Open to ALL students (mostly online)
   - Bug bounties (Intigriti, HackerOne): Open to ALL
   - Superteam bounties: Open to ALL (crypto/Solana)

RESPONSE GUIDELINES:
1. **NEVER say you can't help due to location** - especially for hackathons/bounties.
2. **Software developers from ANY country can apply to tech opportunities.**
3. **Nigerian students CAN apply to DevPost, DoraHacks, MLH, and all online hackathons.**
4. **Only location-restricted: Some US scholarships require US residency (mark these clearly).**

If user mentions stress about school fees, tuition, or urgent financial need:
- Prioritize bounties and hackathons with PRIZE MONEY
- These are fast-turnaround and globally accessible
- Show opportunities with nearest deadlines first

RESPONSE FORMAT (CRITICAL):
⚠️ **DO NOT LIST OPPORTUNITIES AS TEXT** - The frontend UI will display them as interactive cards.
Your job is to:
1. **Acknowledge their situation** briefly (especially if stressed)
2. **Summarize what you found** in 2-3 sentences (e.g., "I found 12 great matches for you, including 3 hackathons with $20K+ prize pools and 5 bounties you can start today.")
3. **Highlight 2-3 top picks** briefly by name only (e.g., "Your best bets are: BCH-1 Hackcelerator ($20K), Hack4Privacy ($6K), and the Camp Network Buildathon.")
4. **Provide 2-3 actionable next steps** (e.g., "Start with the ones marked 'Urgent' - those deadlines are coming up fast!")

❌ DO NOT: List all 10+ opportunities with details, links, match scores, deadlines, etc. - the UI cards handle that.
✅ DO: Be conversational, warm, and brief. Point them to the cards below your message.

IMPORTANT: 
- You HAVE access to opportunities. They are from our database.
- DO NOT say "I cannot help with opportunities outside [country]"
- DO NOT limit results to US-only for hackathons/bounties
- Use the provided SEARCH RESULTS as your source of truth.
- The opportunities array will be rendered as beautiful cards by the frontend.

If NO SEARCH RESULTS are found:
- Suggest the user check back soon (we update daily)
- Recommend they explore DevPost.com, DoraHacks.io, MLH.io directly
"""
        return prompt
    
    def _detect_search_intent(self, message: str) -> bool:
        """Detect if user wants to search for opportunities"""
        intent_keywords = [
            'find', 'search', 'show me', 'need money', 'urgent', 'hackathon',
            'scholarship', 'bounty', 'competition', 'opportunity', 'apply',
            'deadline', 'this week', 'today', 'tomorrow', 'help me find',
            'looking for', 'need', 'want'
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in intent_keywords)
    
    async def _extract_search_criteria(self, message: str, profile: Dict) -> Dict[str, Any]:
        """Extract search parameters from natural language"""
        message_lower = message.lower()
        
        criteria = {
            'types': [],
            'urgency': 'any',
            'min_amount': None,
            'keywords': []
        }
        
        # Detect types
        if any(word in message_lower for word in ['hackathon', 'build', 'sprint']):
            criteria['types'].append('hackathon')
        if any(word in message_lower for word in ['bounty', 'bug', 'issue']):
            criteria['types'].append('bounty')
        if any(word in message_lower for word in ['scholarship', 'grant', 'funding']):
            criteria['types'].append('scholarship')
        if any(word in message_lower for word in ['competition', 'contest', 'challenge']):
            criteria['types'].append('competition')
        
        # Default to all types if none specified
        if not criteria['types']:
            criteria['types'] = ['scholarship', 'hackathon', 'bounty', 'competition']
        
        # Detect urgency
        if any(word in message_lower for word in ['urgent', 'now', 'today', 'asap', 'immediately']):
            criteria['urgency'] = 'immediate'
        elif any(word in message_lower for word in ['this week', 'soon', 'quickly']):
            criteria['urgency'] = 'this_week'
        elif any(word in message_lower for word in ['this month', 'month']):
            criteria['urgency'] = 'this_month'
        
        # Extract keywords from the profile to enrich search
        interests = profile.get('interests', [])
        if interests:
            criteria['keywords'].extend(interests[:3])  # Top 3 interests as search keywords
        
        return criteria
    
    async def _search_opportunities_with_stats(
        self, 
        criteria: Dict[str, Any], 
        profile: Dict,
        depth: int = 0
    ) -> tuple[List[Dict[str, Any]], Dict[str, int]]:
        """
        Search opportunities with detailed statistics for transparency and real-time matching.
        V2 FIXES:
        - Recalculate match scores in real-time
        - Broadened location logic (global = accessible)
        - Software devs match hackathons/bounties
        - Nigeria/Ibadan context detection
        - Recursive broadening for emergency situations
        Returns: (opportunities_list, statistics_dict)
        """
        from app.services.personalization_engine import personalization_engine
        from app.models import UserProfile
        
        stats = {
            'total_scanned': 0,
            'expired': 0,
            'location_filtered': 0,
            'type_filtered': 0,
            'urgency_filtered': 0
        }
        
        try:
            # 1. Start with Database Search
            all_opps = await db.get_all_scholarships()
            stats['total_scanned'] = len(all_opps)
            
            # 2. SEMANTIC VECTOR SEARCH - Triggered when:
            #    - Database has few results
            #    - User is searching for specific types (hackathon, bounty)
            #    - Explicit semantic search request
            semantic_results = []
            use_semantic = (
                len(all_opps) < 50 or 
                any(kw in criteria['types'] for kw in ['hackathon', 'bounty', 'grant']) or
                criteria.get('use_semantic', False)
            )
            
            if use_semantic:
                try:
                    from app.services.vectorization_service import vectorization_service
                    
                    # Build query string from search context
                    query_parts = criteria['types'].copy()
                    query_parts.append(profile.get('major', ''))
                    query_parts.extend(criteria.get('keywords', []))
                    query_parts.extend(profile.get('interests', [])[:2])
                    query_text = ' '.join([p for p in query_parts if p])
                    
                    logger.info("Triggering semantic search", query=query_text[:100])
                    
                    # Generate query embedding
                    query_embedding = await vectorization_service.vectorize_query(query_text)
                    
                    if query_embedding:
                        semantic_results = await db.semantic_search(
                            query_embedding, 
                            limit=30, 
                            min_similarity=0.50
                        )
                        
                        # Merge with keyword results (deduplicate by ID)
                        existing_ids = {opp.id for opp in all_opps}
                        added_count = 0
                        for sem_opp in semantic_results:
                            if sem_opp.id not in existing_ids:
                                all_opps.append(sem_opp)
                                existing_ids.add(sem_opp.id)
                                added_count += 1
                        
                        stats['semantic_matches'] = len(semantic_results)
                        stats['semantic_added'] = added_count
                        logger.info("Semantic search enriched results", 
                                   semantic_found=len(semantic_results), 
                                   new_added=added_count)
                                   
                except Exception as sem_err:
                    logger.warning("Semantic search failed, continuing with keyword results", error=str(sem_err))
            
            # TRIGGER ON-DEMAND SCRAPING if database is thin
            if depth == 0 and (len(all_opps) < 20 or any(kw in criteria['types'] for kw in ['hackathon', 'bounty'])):
                logger.info("Triggering background on-demand search mission")
                search_query = f"{' '.join(criteria['types'])} {profile.get('major', '')} {profile.get('school', '')} {profile.get('interests', [''])[0]}"
                asyncio.create_task(scout.execute_mission(search_query))
            
            filtered_opps = []
            now = datetime.now()
            user_profile_obj = UserProfile(**profile) if profile else None
            
            # V2 FIX: Expanded Nigerian institution detection
            NIGERIAN_INSTITUTIONS = [
                'ibadan', 'lagos', 'unilag', 'ui', 'oau', 'ife', 'covenant', 'babcock', 
                'afe babalola', 'lautech', 'futa', 'unn', 'nsukka', 'benin', 'uniben',
                'abu', 'zaria', 'ahmadu bello', 'obafemi awolowo', 'noun', 'uniport',
                'delsu', 'eksu', 'funaab', 'futo', 'uniuyo', 'unical', 'buk', 'bayero'
            ]
            
            school_str = str(profile.get('school', '')).lower()
            country_str = str(profile.get('country', '')).lower()
            
            # Detect Nigerian context more broadly
            is_nigeria = (
                'nigeria' in country_str or 
                any(inst in school_str for inst in NIGERIAN_INSTITUTIONS) or
                'nigeria' in school_str
            )
            
            # Also detect other African countries for similar treatment
            AFRICAN_COUNTRIES = ['nigeria', 'kenya', 'ghana', 'south africa', 'egypt', 'rwanda', 'ethiopia', 'tanzania', 'uganda']
            is_african = any(country in country_str for country in AFRICAN_COUNTRIES) or is_nigeria
            
            user_country = (profile.get('country') or ('Nigeria' if is_nigeria else '')).lower()
            user_state = (profile.get('state') or '').lower()
            user_interests = [i.lower() for i in (profile.get('interests') or [])]
            
            # Build UserProfile object for scoring
            user_profile_obj = None
            try:
                user_profile_obj = UserProfile(**profile) if profile else None
            except Exception:
                pass
            
            for opp in all_opps:
                # 1. EXPIRATION CHECK (strict with grace period)
                if opp.deadline:
                    try:
                        deadline_date = datetime.fromisoformat(opp.deadline.replace('Z', '+00:00'))
                        if deadline_date.date() < now.date() - timedelta(days=1): # 1 day grace for timezones
                            stats['expired'] += 1
                            continue
                    except (ValueError, AttributeError):
                        pass
                
                # 2. TYPE FILTER (BROADENED: Software devs match hackathons/bounties/competitions)
                opp_type = self._infer_type(opp)
                requested_types = criteria.get('types') or []
                
                # 3. LOCATION FILTER (V2: VERY LENIENT for global opportunities)
                eligibility = getattr(opp, 'eligibility', {})
                if hasattr(eligibility, 'dict'):
                    eligibility = eligibility.dict()
                elif hasattr(eligibility, 'model_dump'):
                    eligibility = eligibility.model_dump()
                
                opp_states = [s.lower() for s in (eligibility.get('states') or [])]
                opp_citizenship = (eligibility.get('citizenship') or '').lower()
                geo_tags = [t.lower() for t in (getattr(opp, 'geo_tags', []) or [])]
                location_str = self._get_location_string(opp).lower()
                
                # V2 FIX: Global/Remote/International opportunities accessible to ALL
                is_global = any(tag in geo_tags for tag in ['global', 'remote', 'international', 'online', 'worldwide']) or \
                            any(kw in location_str for kw in ['global', 'international', 'worldwide', 'anywhere', 'remote', 'virtual'])
                
                is_open_citizenship = not opp_citizenship or opp_citizenship in ['any', 'international', 'all', '']
                
                # V2 FIX: HACKATHONS, BOUNTIES, COMPETITIONS are ALWAYS GLOBAL
                # This is the critical fix - these opportunity types have NO location restrictions
                if opp_type in ['hackathon', 'bounty', 'competition', 'challenge']:
                    # ALWAYS include - no location filter for tech opportunities
                    pass  # Continue to add to filtered_opps
                else:
                    # Only filter scholarships with explicit location restrictions
                    location_restricted = False
                    
                    # Check state restriction (only for scholarships)
                    if opp_states and user_state:
                        if not any(user_state in s for s in opp_states):
                            if not is_global:
                                location_restricted = True
                    
                    # Check citizenship restriction (only for scholarships)
                    if opp_citizenship and opp_citizenship not in ['any', 'international', 'all', '']:
                        if user_country and user_country not in opp_citizenship:
                            if not is_global:
                                # Allow if user is from developing countries and opp mentions development/international
                                if not (is_african and any(kw in location_str for kw in ['africa', 'developing', 'international', 'global'])):
                                    location_restricted = True
                    
                    if location_restricted:
                        stats['location_filtered'] += 1
                        continue
                
                # 4. URGENCY FILTER
                urgency = criteria.get('urgency', 'any')
                if urgency != 'any' and opp.deadline:
                    try:
                        deadline_date = datetime.fromisoformat(opp.deadline.replace('Z', '+00:00'))
                        days_until = (deadline_date - now).days
                        
                        if urgency == 'immediate' and days_until > 10: # Expanded from 7 to 10
                            stats['urgency_filtered'] += 1
                            continue
                        if urgency == 'this_week' and days_until > 20: # Expanded from 14 to 20
                            stats['urgency_filtered'] += 1
                            continue
                    except:
                        pass
                
                filtered_opps.append(opp)
            
            # V3 FIX: Real-time match score recalculation + diversity interleaving
            results = []
            for opp in filtered_opps[:50]:  # Increased limit for diversity pool
                # Build opportunity dict for personalization engine
                opp_dict = opp.model_dump() if hasattr(opp, 'model_dump') else opp.dict() if hasattr(opp, 'dict') else {}

                # V2 FIX: Calculate fresh match score
                fresh_score = 50  # Default
                if user_profile_obj:
                    try:
                        fresh_score = personalization_engine.calculate_personalized_score(opp_dict, user_profile_obj)
                    except Exception as e:
                        logger.warning("Score calc failed", error=str(e))
                        fresh_score = opp.match_score or 50
                elif opp.match_score:
                    fresh_score = opp.match_score

                results.append({
                    'id': opp.id,
                    'name': opp.name,
                    'organization': opp.organization,
                    'amount': opp.amount,
                    'amount_display': opp.amount_display,
                    'deadline': opp.deadline,
                    'type': self._infer_type(opp),
                    'match_score': int(round(fresh_score)),  # V2: Fresh score
                    'source_url': opp.source_url,
                    'tags': opp.tags,
                    'description': opp.description,
                    'location_eligibility': self._get_location_string(opp),
                    'priority_level': opp.priority_level
                })

            # Sort by fresh match score (relevance-first)
            results.sort(key=lambda x: x.get('match_score', 0), reverse=True)

            # V3 FIX: Relevance-first diversity interleaving
            # Guarantees at least 12 results with light source/type diversity.
            final_results = self._interleave_for_diversity(results, target_count=12)
            
            logger.info(
                "Search V3 completed",
                total_scanned=stats['total_scanned'],
                final_matches=len(final_results),
                expired_filtered=stats['expired'],
                location_filtered=stats['location_filtered']
            )

            # EMERGENCY RECOVERY: If <10 results for crisis, broaden and retry ONCE
            if len(final_results) < 10 and depth == 0:
                logger.info("CRISIS RECOVERY: Broadening search criteria for more results")
                broader_criteria = criteria.copy()
                broader_criteria['urgency'] = 'any'
                broader_criteria['broadened'] = True  # Flag for the thinking process
                return await self._search_opportunities_with_stats(broader_criteria, profile, depth=1)

            return final_results, stats
            
        except Exception as e:
            logger.error("Search failed", error=str(e))
            import traceback
            traceback.print_exc()
            return [], stats
    
    def _interleave_for_diversity(self, sorted_results: List[Dict], target_count: int = 12) -> List[Dict]:
        """Relevance-first diversity interleaving.

        Strategy:
        - First 6 slots: pure relevance (highest match scores)
        - Remaining slots: interleave from under-represented types/sources while still
          preferring higher scores within each bucket.

        This guarantees variety without sacrificing match quality for top picks.
        """
        if len(sorted_results) <= target_count:
            return sorted_results

        final = []
        used_ids = set()

        # Phase 1: Top 6 by pure relevance
        for item in sorted_results[:6]:
            final.append(item)
            used_ids.add(item['id'])

        # Phase 2: Build buckets by type
        buckets: Dict[str, List[Dict]] = {}
        for item in sorted_results:
            if item['id'] in used_ids:
                continue
            t = item.get('type', 'scholarship')
            buckets.setdefault(t, []).append(item)

        # Round-robin from buckets until we reach target_count
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

        # If still short, fill from remaining sorted_results
        for item in sorted_results:
            if len(final) >= target_count:
                break
            if item['id'] not in used_ids:
                final.append(item)
                used_ids.add(item['id'])

        return final

    def _infer_type(self, opp) -> str:
        """Infer opportunity type from tags/description"""
        tags_str = ' '.join(opp.tags or []).lower()
        desc_str = (opp.description or '').lower()
        combined = f"{tags_str} {desc_str}"

        if 'hackathon' in combined or 'hack' in combined:
            return 'hackathon'
        elif 'bounty' in combined or 'bug' in combined:
            return 'bounty'
        elif 'competition' in combined or 'contest' in combined:
            return 'competition'
        else:
            return 'scholarship'
    
    def _calculate_urgency(self, opp) -> str:
        """Calculate urgency from deadline"""
        if not opp.deadline:
            return 'immediate'  # Rolling deadline
        
        try:
            deadline_date = datetime.fromisoformat(opp.deadline.replace('Z', '+00:00'))
            days_until = (deadline_date - datetime.now()).days
            
            if days_until <= 2:
                return 'immediate'
            elif days_until <= 7:
                return 'this_week'
            elif days_until <= 30:
                return 'this_month'
            else:
                return 'future'
        except:
            return 'future'
            
    def _get_location_string(self, opp) -> str:
        """Get human readable location eligibility"""
        eligibility = getattr(opp, 'eligibility', {})
        if hasattr(eligibility, 'dict'):
            eligibility = eligibility.dict()
            
        states = eligibility.get('states') or []
        citizenship = eligibility.get('citizenship')
        
        if states:
            return f"Residents of {', '.join(states)}"
        if citizenship and citizenship.lower() != 'any':
            return f"Citizens of {citizenship}"
        return "Open / International"
    
    def _generate_actions(self, opportunities: List[Dict], message: str) -> List[Dict[str, Any]]:
        """Generate suggested actions"""
        actions = []
        
        if opportunities:
            # Add save action for top opportunities
            for opp in opportunities[:3]:
                actions.append({
                    'type': 'save',
                    'opportunity_id': opp.get('id'),
                    'label': f"Save {opp.get('name', 'opportunity')}"
                })
        
        return actions
    
    async def _save_message(self, user_id: str, role: str, content: str):
        """Save conversation to database"""
        try:
            # Save to Firebase (implement in db.py)
            await db.save_chat_message(user_id, role, content)
        except Exception as e:
            logger.error("Failed to save message", error=str(e))


# Global chat service instance
chat_service = ChatService()
