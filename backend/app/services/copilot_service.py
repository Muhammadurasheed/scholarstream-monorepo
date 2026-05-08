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
You are the ScholarStream Co-Pilot: **{platform_persona['name']}**
Expertise: {platform_persona.get('expertise', 'opportunity applications')}

=== KNOWLEDGE BASE ===

{profile_section}

{doc_section}

CURRENT PAGE:
- Platform: {platform_persona['name']}
- URL: {page_url}

=== INSTRUCTIONS ===
1. **BE EXTREMELY CONCISE.** The user is in a small sidepanel. Do not write essays here.
2. If the user asks to "draft", "write", or "fill" something, provide a **SHORT 1-2 sentence overview/insight** and then **DIRECT them to use the ✨ Sparkle icon** on the page fields for the full drafting.
3. Use ONLY the knowledge base. Extract specific details.
4. If no relevant documents exist, suggest uploading one.

=== OUTPUT FORMAT (JSON) ===
{{
  "thought_process": "Brief reasoning",
  "message": "Your response. KEEP IT UNDER 3 SMALL PARAGRAPHS. Be direct. If drafting, give a tiny insight + 'Use the ✨ Sparkle on the page for the full draft!'",
  "action": null,
  "coaching_tips": []
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

    # Platform-specific length directives (words)
    PLATFORM_LENGTH_HINTS = {
        'devpost.com': {
            'elevator_pitch': (100, 200),
            'description': (800, 2500),
            'inspiration': (300, 600),
            'technical': (500, 1500),
            'challenges': (300, 800),
            'accomplishments': (300, 800),
            'next_steps': (200, 500),
            'generic': (300, 800),
        },
        'dorahacks.io': {
            'description': (500, 1500),
            'technical': (400, 1000),
            'generic': (300, 800),
        },
        'default': {
            'elevator_pitch': (50, 150),
            'description': (200, 800),
            'generic': (100, 400),
        }
    }

    def _get_length_directive(self, platform_url: str, field_category: str, char_limit: int = None, word_limit: int = None) -> str:
        """Get platform-aware length directive for a field."""
        if char_limit:
            return f"HARD LIMIT: Response MUST be under {char_limit} characters. Count carefully."
        if word_limit:
            return f"Target approximately {word_limit} words."

        # Infer from platform + field category
        parsed = urlparse(platform_url) if platform_url else None
        domain = parsed.netloc.lower().replace('www.', '') if parsed else ''

        hints = self.PLATFORM_LENGTH_HINTS.get(domain, self.PLATFORM_LENGTH_HINTS['default'])
        min_words, max_words = hints.get(field_category, hints.get('generic', (100, 400)))

        return f"Write {min_words}-{max_words} words. Be comprehensive and detailed."

    async def generate_field_content(
        self, 
        target_field: Dict[str, Any], 
        user_profile: Dict[str, Any], 
        instruction: Optional[str] = None,
        page_url: Optional[str] = None,
        project_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sparkle V4 — Direct Content Generation (No JSON overhead).
        
        KEY CHANGE: The AI generates raw content text directly, not wrapped in JSON.
        This gives the full token budget to actual content instead of schema overhead.
        """
        platform_persona = self._detect_platform(page_url or '')
        
        # Extract field constraints
        char_limit = target_field.get('characterLimit')
        word_limit = target_field.get('wordLimit')
        field_format = target_field.get('format', 'plain')
        field_category = target_field.get('fieldCategory', 'generic')
        
        # Platform-aware length directive
        length_directive = self._get_length_directive(page_url, field_category, char_limit, word_limit)
        
        # Format directive
        if field_format == 'markdown':
            format_directive = "Use clean Markdown: **bold** for key terms, bullet lists for multiple items, paragraph breaks for readability. No excessive formatting."
        else:
            format_directive = "STRICT PLAIN TEXT. No markdown symbols (no **, #, `, _). Use clean sentence structure and natural emphasis through word choice."

        prompt = f"""You are a world-class application writer specializing in {platform_persona.get('expertise', 'opportunity applications')}.

TASK: Write the content for the "{target_field.get('label', field_category)}" field.

=== YOUR KNOWLEDGE BASE ===

User Background:
{json.dumps(user_profile, indent=2) if user_profile else 'Not provided.'}

Project/Document Context:
{project_context[:50000] if project_context else 'No project document provided. Use the user background to write compelling content.'}

=== FIELD REQUIREMENTS ===
- Field: {target_field.get('label')} ({field_category.replace('_', ' ').title()})
- Context: {target_field.get('surroundingContext', 'N/A')}
- Length: {length_directive}
- Format: {format_directive}

=== SPECIAL INSTRUCTIONS ===
{instruction or 'Write authentic, high-impact content.'}

=== RULES ===
1. Use SPECIFIC details from the knowledge base — exact project names, technologies, metrics.
2. Never invent facts not present in the knowledge base.
3. Write in first person, as if the applicant is writing.
4. Make it sound human and authentic, not AI-generated.
5. Match the tone to the platform ({platform_persona['name']}).

Write ONLY the field content below. No preamble, no explanations, no JSON wrapping — just the content itself:
"""
        try:
            # Use the long-form generation method for maximum output
            result = await ai_service.generate_long_content_async(prompt)
            
            if not result or not result.strip():
                raise ValueError("Empty response from AI")

            content = result.strip()
            
            # Clean any accidental AI preamble
            preamble_patterns = [
                'here is', 'here\'s', 'sure,', 'certainly', 'of course',
                'below is', 'the content:', 'here is the content'
            ]
            first_line = content.split('\n')[0].lower()
            if any(first_line.startswith(p) for p in preamble_patterns):
                # Remove the preamble line
                content = '\n'.join(content.split('\n')[1:]).strip()
            
            # Strip wrapping quotes
            if content.startswith('"') and content.endswith('"'):
                content = content[1:-1].strip()
            
            # Enforce character limit if specified
            if char_limit and len(content) > char_limit:
                truncated = content[:char_limit-3].rsplit(' ', 1)[0] + '...'
                content = truncated
                logger.info("Sparkle content truncated to meet char limit", 
                           original=len(result), truncated=len(content), limit=char_limit)
            
            # Build reasoning deterministically (no AI tokens wasted on this)
            reasoning_parts = []
            if project_context:
                reasoning_parts.append(f"Based on uploaded document ({len(project_context)} chars)")
            if user_profile:
                reasoning_parts.append("profile data included")
            reasoning_parts.append(f"{field_format} format")
            reasoning = " | ".join(reasoning_parts)

            return {
                "content": content,
                "reasoning": reasoning
            }
        except Exception as e:
            logger.error("Sparkle generation failed", error=str(e))
            return {
                "content": "",
                "reasoning": f"Generation failed: {str(e)[:100]}"
            }


copilot_service = CopilotService()

