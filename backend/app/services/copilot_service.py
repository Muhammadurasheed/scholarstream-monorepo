"""
ScholarStream Co-Pilot V2: Context-Aware Application Assistant

IMPORTANT: This service receives project_context from the extension which contains
the FULL TEXT content of uploaded documents (PDF, DOCX, TXT). The extension parses
these documents client-side or via /api/documents/parse and sends the text content.

KEY UPGRADES:
1. Platform Detection: Knows if user is on DevPost, DoraHacks, etc.
2. Tri-Fold Knowledge Base: User Profile + Uploaded Docs + Page Context
3. Platform-Specific Coaching: Tailored advice for each application platform
"""

import structlog
from typing import Dict, Any, List, Optional
import json
from urllib.parse import urlparse

from app.services.ai_service import ai_service
from app.config import settings

logger = structlog.get_logger()


class CopilotService:
    
    # Platform-specific expert personas
    PLATFORM_PERSONAS = {
        'devpost.com': {
            'name': 'DevPost Hackathon Coach',
            'expertise': 'DevPost hackathon submissions, project showcases, team formation',
            'tips': [
                'Focus on the "What it does" section - judges skim this first',
                'Include a demo video - projects with videos get 3x more views',
                'Tag technologies accurately for sponsor prizes',
                'Highlight the "How we built it" with specific tech challenges overcome'
            ]
        },
        'dorahacks.io': {
            'name': 'DoraHacks BUIDL Expert',
            'expertise': 'DoraHacks BUIDLs, Web3 hackathons, blockchain projects',
            'tips': [
                'Emphasize on-chain components and smart contract innovation',
                'Include GitHub repo and deployed contract addresses',
                'Focus on the Web3 primitives used (DeFi, NFTs, DAOs)',
                'Highlight team experience in blockchain development'
            ]
        },
        'mlh.io': {
            'name': 'MLH Hackathon Mentor',
            'expertise': 'Major League Hacking events, beginner-friendly hackathons',
            'tips': [
                'MLH judges value learning journey over polish',
                'Document what you learned, not just what you built',
                'Engage with sponsor challenges for bonus prizes',
                'Team size matters - 2-4 is optimal'
            ]
        },
        'angelhack.com': {
            'name': 'AngelHack Accelerator Coach',
            'expertise': 'AngelHack hackathons related accelerator programs',
            'tips': [
                'Focus on market viability and business model',
                'AngelHack values founder potential',
                'Include user validation or early traction',
                'Pitch deck quality matters here'
            ]
        },
        'gitcoin.co': {
            'name': 'Gitcoin Grants Advisor',
            'expertise': 'Gitcoin grants, quadratic funding, public goods',
            'tips': [
                'Emphasize public goods and open source impact',
                'Community engagement metrics matter for QF',
                'Include clear milestones and deliverables',
                'Previous contribution history helps credibility'
            ]
        },
        'hackerone.com': {
            'name': 'Bug Bounty Specialist',
            'expertise': 'HackerOne bug bounty submissions, vulnerability reports',
            'tips': [
                'Be specific about vulnerability type (OWASP classification)',
                'Include clear reproduction steps',
                'Explain business impact in terms of risk',
                'Provide proof-of-concept but avoid destructive testing'
            ]
        },
        'immunefi.com': {
            'name': 'Web3 Security Researcher',
            'expertise': 'Smart contract auditing, DeFi security, blockchain vulnerabilities',
            'tips': [
                'Focus on fund-at-risk calculations',
                'Reference similar past vulnerabilities',
                'Include on-chain evidence and transaction hashes',
                'Explain attack vectors in detail'
            ]
        },
        'kaggle.com': {
            'name': 'Kaggle Competition Expert',
            'expertise': 'Data science competitions, ML model optimization',
            'tips': [
                'Document your approach in a clear notebook',
                'Ensemble methods often win',
                'Feature engineering is key',
                'Validate with robust cross-validation'
            ]
        }
    }
    
    def _detect_platform(self, url: str) -> Dict[str, Any]:
        """Detect which platform the user is on and return persona"""
        if not url:
            return {'name': 'General Application Assistant', 'tips': []}
        
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace('www.', '')
        
        for platform_domain, persona in self.PLATFORM_PERSONAS.items():
            if platform_domain in domain:
                return persona
        
        return {
            'name': 'General Application Assistant',
            'expertise': 'Scholarship and hackathon applications',
            'tips': [
                'Be specific about your achievements with metrics',
                'Connect your experience to the opportunity requirements',
                'Show genuine enthusiasm for the specific opportunity'
            ]
        }
    
    async def chat(self, 
                   query: str, 
                   page_context: Dict[str, Any], 
                   project_context: Optional[str] = None,
                   user_profile: Optional[Dict[str, Any]] = None,
                   mentioned_docs: Optional[List[str]] = None,
                   include_profile: bool = True) -> Dict[str, Any]:
        """
        Main chat handler V2 - Now with FAANG-level knowledge base control.
        
        STRICT KNOWLEDGE BASE RULES:
        1. If @mentions provided: ONLY use those specific documents
        2. Profile inclusion is controlled by toggle (include_profile flag)
        3. If no mentions and no profile: Suggest user upload docs or complete profile
        """
        
        # V2: Detect platform and get specialized persona
        page_url = page_context.get('url', '')
        platform_persona = self._detect_platform(page_url)
        
        # V2: Build knowledge base section based on what's provided
        # Sanitize project context from internal placeholders or errors
        sanitized_context = project_context or ""
        error_placeholders = ["[PDF content", "[DOCX content", "please install"]
        if any(p in sanitized_context for p in error_placeholders):
            logger.warning("Sanitizing project context: Removing placeholders")
            for p in error_placeholders:
                # Remove lines containing placeholders
                lines = sanitized_context.split('\n')
                sanitized_context = '\n'.join([l for l in lines if p not in l])

        has_project_docs = sanitized_context and len(sanitized_context.strip()) > 50
        
        # Log KB state for debugging
        logger.info(
            "Copilot chat KB state",
            has_project_docs=has_project_docs,
            project_context_length=len(sanitized_context) if sanitized_context else 0,
            mentioned_docs=mentioned_docs,
            include_profile=include_profile,
            has_user_profile=bool(user_profile)
        )
        
        # Build document context info with EMPHASIS
        doc_section = ""
        if has_project_docs:
            if mentioned_docs and len(mentioned_docs) > 0:
                doc_section = f"""✅ **EXPLICITLY MENTIONED DOCUMENTS** ({len(mentioned_docs)} docs): {', '.join(mentioned_docs)}
 
⚠️ CRITICAL: YOU MUST USE THIS DOCUMENT CONTENT BELOW TO ANSWER THE USER'S QUESTION.
DO NOT MAKE UP INFORMATION. USE THE ACTUAL CONTENT PROVIDED HERE:
 
=== BEGIN DOCUMENT CONTENT ===
{sanitized_context}
=== END DOCUMENT CONTENT ===
 
If the user is asking you to fill a field or help with an application, extract specific details 
from the document content above (names, skills, experiences, projects) and use them verbatim."""
            else:
                doc_section = f"""✅ DOCUMENTS AVAILABLE (Use this content):
 
=== BEGIN DOCUMENT CONTENT ===
{sanitized_context}
=== END DOCUMENT CONTENT ==="""
        else:
            doc_section = "❌ No valid project documents found. Suggest user upload their resume/project README using the + button."
        
        # Build profile section
        profile_section = ""
        if include_profile and user_profile:
            profile_section = f"""✅ USER PROFILE (INCLUDED - use this information):
{json.dumps(user_profile, indent=2)}"""
        elif include_profile and not user_profile:
            profile_section = "⚠️ Profile was requested but not available."
        else:
            profile_section = "❌ USER PROFILE (EXCLUDED by user preference) - DO NOT use any profile data. Only use document content."
        
        prompt = f"""
You are the ScholarStream Co-Pilot V2: **{platform_persona['name']}**

You are an elite AI agent with deep expertise in: {platform_persona.get('expertise', 'opportunity applications')}

=== KNOWLEDGE BASE (STRICTLY USE ONLY WHAT'S PROVIDED) ===

1️⃣ {profile_section}

2️⃣ PROJECT DOCUMENTS:
{doc_section}

3️⃣ CURRENT PAGE CONTEXT:
- Platform: {platform_persona['name']}
- URL: {page_url}
- Page Title: {page_context.get('title', 'Unknown')}
- Visible Content (Truncated): {page_context.get('content', '')[:40000]}

=== PLATFORM-SPECIFIC TIPS ===
{chr(10).join(f"• {tip}" for tip in platform_persona.get('tips', []))}

=== USER QUERY ===
"{query}"

=== YOUR TASK ===
1. **Analyze** the user's query in context of the provided knowledge base
2. **Use ONLY provided context**: If documents were provided, you MUST extract specific information from them.
3. **DO NOT HALLUCINATE**: Never make up names, skills, or experiences. Use exactly what's in the documents.
4. **If profile is excluded, do NOT infer profile data** - only use document content
5. **Determine Intent**:
   - Q&A: Answer questions about the opportunity/platform
   - DRAFTING: Write essays, cover letters, short answers using the PROVIDED document content
   - COACHING: Provide strategic advice for winning this specific type of opportunity
   - FILLING: Generate field auto-fill actions when explicitly requested
6. **Personalize**: Reference SPECIFIC details from the provided documents (if any)
7. **Platform Expertise**: Apply your specialized knowledge of this platform's judging criteria

=== OUTPUT FORMAT (JSON ONLY) ===
{{
  "thought_process": "Brief internal reasoning about which document/profile data you're using",
  "message": "Your response to the user. Be helpful, specific, and actionable. Reference specific info from documents.",
  "action": {{
    "type": "fill_field",
    "selector": "css_selector",
    "value": "content"
  }} OR null,
  "coaching_tips": ["Optional strategic tips specific to this platform"]
}}
"""
        try:
            result = await ai_service.generate_content_async(prompt)
            
            if not result:
                raise ValueError("Empty response from AI Service")

            # Parse JSON with robust cleanup
            text = result.strip()
            if text.startswith('```json'):
                text = text[7:]
            if text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            text = text.strip()
            
            response_data = json.loads(text)
            
            return {
                "message": response_data.get("message", "I processed that for you."),
                "action": response_data.get("action"),
                "coaching_tips": response_data.get("coaching_tips", []),
                "platform": platform_persona['name']
            }
            
        except json.JSONDecodeError:
            logger.error("Copilot JSON Parse Error", raw_result=result[:200] if result else "None")
            return {
                "message": f"I understood your request. {result[:500] if result else 'Please try again.'}",
                "action": None,
                "platform": platform_persona['name']
            }
        except Exception as e:
            error_msg = str(e)
            logger.error("Copilot chat failed", error=error_msg)
            
            # FAANG-grade: Return actionable hints for specific failures
            hint = "I'm having trouble connecting to my brain right now."
            if "429" in error_msg or "quota" in error_msg.lower():
                hint = "My brain is a bit overwhelmed (Rate Limit). Please try again in a few seconds."
            elif "403" in error_msg:
                hint = "I'm having trouble accessing my intelligence core (Auth/Key issue)."
            
            return {
                "message": f"{hint} (Ref: {error_msg[:50]})",
                "action": None,
                "platform": platform_persona['name']
            }

    async def generate_field_content(
        self, 
        target_field: Dict[str, Any], 
        user_profile: Dict[str, Any], 
        instruction: Optional[str] = None,
        page_url: Optional[str] = None,
        project_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sparkle V3 / Focus Fill Handler - Now with full TRI-FOLD knowledge base.
        Generates content for a SINGLE specific field with high precision.
        
        TRI-FOLD KNOWLEDGE:
        1. User Profile (skills, background, experience)
        2. Project Context (uploaded document)
        3. Field Context (what the field needs)
        """
        platform_persona = self._detect_platform(page_url or '')
        
        # Extract field constraints
        char_limit = target_field.get('characterLimit')
        word_limit = target_field.get('wordLimit')
        field_format = target_field.get('format', 'plain')
        field_category = target_field.get('fieldCategory', 'generic')
        
        # Build constraint instructions
        constraints = []
        if char_limit:
            constraints.append(f"⚠️ HARD LIMIT: Response MUST be under {char_limit} characters. Count carefully!")
        if word_limit:
            constraints.append(f"📝 Aim for approximately {word_limit} words.")
        if field_format == 'markdown':
            constraints.append("📑 Format: Use markdown (bold, lists) for better readability.")
        
        constraint_text = "\n".join(constraints) if constraints else "No specific length constraints."
        
        # Apple-grade Formatting Directives
        format_guardrail = ""
        if field_format == 'markdown':
            format_guardrail = """
📑 FORMATTING (MARKDOWN):
- Use "Magazine-Quality" Markdown.
- Employ Bold tags (**bold**) for highlighting key technical terms or impact metrics.
- Use Bulleted lists for clarity if multiple items are listed.
- Ensure balanced whitespace and professional paragraph breaks.
"""
        else:
            format_guardrail = """
🚫 FORMATTING (STRICT PLAIN TEXT - ZERO-MD POLICY):
- DO NOT use any markdown symbols. NO asterisks (**), NO hashes (#), NO backticks (`), NO underscores (_).
- Use only standard capitalization and punctuation for emphasis.
- Ensure perfect, clean typography.
"""

        prompt = f"""
You are the "{platform_persona['name']}" Einstein-Socrates Engine for ScholarStream. 
Your purpose is to draft "Distinguished Engineer" grade content for application fields.

=== TRIAD KNOWLEDGE BASE ===

1️⃣ PORTFOLIO (User Background):
{json.dumps(user_profile, indent=2) if user_profile else "Not provided - focus on project context."}

2️⃣ VERACITY SOURCE (Project Context):
{project_context[:25000] if project_context else "No project document provided. Draft compelling content using the profile."}

3️⃣ INSTRUCTIONAL INTENT:
{instruction or "Draft a high-impact response for this field."}

=== FIELD SPECIFICS ===
- Category: {field_category.replace('_', ' ').title()}
- Label/Context: {target_field.get('label')} | {target_field.get('surroundingContext', '')}
- Constraints: {constraint_text}
{format_guardrail}

=== DISTINGUISHED ENGINE DIRECTIVES ===
1. EINSTEIN GROUNDING: Your response MUST be a direct derivation of the VERACITY SOURCE. Use EXACT high-fidelity terms (e.g., "Confluent Flink", "Vertex AI").
2. ZERO HALLUCINATION: If a fact is not in the Triad KB, do NOT invent it. Bridge gaps with professional logic.
3. SOCRATIC INTENT: Answer the *intent* of the question. For "Challenges", narrate a journey of technical resilience.
4. APPLE-GRADE QUALITY: The content must feel premium, organic, and human-centric. Avoid AI-sounding fluff. Focus on concrete impact.

=== OUTPUT SCHEMA ===
Return ONLY a JSON object:
{{
  "content": "The refined, high-impact text",
  "reasoning": "Context bridge + formatting mode used (Plain/Markdown)"
}}
"""
        try:
            result = await ai_service.generate_content_async(prompt)
            
            # Robust JSON cleanup
            cleaned = result.strip()
            if cleaned.startswith('```json'): cleaned = cleaned[7:]
            if cleaned.startswith('```'): cleaned = cleaned[3:]
            if cleaned.endswith('```'): cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            data = json.loads(cleaned)
            
            # Enforce character limit if specified
            content = data.get('content', '')
            if char_limit and len(content) > char_limit:
                # Truncate intelligently at word boundary
                truncated = content[:char_limit-3].rsplit(' ', 1)[0] + '...'
                data['content'] = truncated
                data['reasoning'] += f" (Truncated from {len(content)} to {len(truncated)} chars)"
                logger.info("Sparkle content truncated to meet char limit", 
                           original=len(content), truncated=len(truncated), limit=char_limit)
            
            return data
        except json.JSONDecodeError as e:
            logger.error("Sparkle JSON parse failed", error=str(e), raw=result[:200] if result else "None")
            # Return raw text as fallback
            return {
                "content": result.strip()[:1000] if result else "",
                "reasoning": "Generated content (JSON parse failed, showing raw output)"
            }
        except Exception as e:
            logger.error("Sparkle generation failed", error=str(e))
            return {
                "content": "",
                "reasoning": f"Generation failed: {str(e)[:100]}"
            }


copilot_service = CopilotService()
