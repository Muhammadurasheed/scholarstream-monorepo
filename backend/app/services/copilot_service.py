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
        has_project_docs = project_context and len(project_context.strip()) > 50
        
        # Log KB state for debugging
        logger.info(
            "Copilot chat KB state",
            has_project_docs=has_project_docs,
            project_context_length=len(project_context) if project_context else 0,
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
{project_context}
=== END DOCUMENT CONTENT ===

If the user is asking you to fill a field or help with an application, extract specific details 
from the document content above (names, skills, experiences, projects) and use them verbatim."""
            else:
                doc_section = f"""✅ DOCUMENTS AVAILABLE (Use this content):

=== BEGIN DOCUMENT CONTENT ===
{project_context}
=== END DOCUMENT CONTENT ==="""
        else:
            doc_section = "❌ No documents provided. Suggest user upload their resume/project README using the + button."
        
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
            logger.error("Copilot chat failed", error=str(e))
            return {
                "message": "I'm having trouble connecting to my brain right now. Please try again in a moment.",
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
        
        prompt = f"""
You are the "{platform_persona['name']}" Sparkle Engine for ScholarStream.
A student needs help filling a specific form field on {platform_persona['name']}.

=== TRI-FOLD KNOWLEDGE BASE ===

1️⃣ USER PROFILE (Who they are):
{json.dumps(user_profile, indent=2) if user_profile else "Not provided - use generic professional tone"}

2️⃣ PROJECT CONTEXT (What they're working on):
{project_context[:20000] if project_context else "No project document uploaded. Generate helpful content based on profile."}

3️⃣ FIELD CONTEXT (What to fill):
- Field Type: {field_category.replace('_', ' ').title()}
- Label: {target_field.get('label')}
- Name/ID: {target_field.get('name')} / {target_field.get('id')}
- Placeholder: {target_field.get('placeholder')}
- Input Type: {target_field.get('type')}
- Platform: {platform_persona['name']}
- Surrounding Context: {target_field.get('surroundingContext', target_field.get('surroundingText', ''))}

=== CONSTRAINTS ===
{constraint_text}

=== ADDITIONAL INSTRUCTIONS ===
{instruction or "Fill this field with compelling, relevant content based on the knowledge base above."}

=== PLATFORM TIPS ===
{chr(10).join(f"• {tip}" for tip in platform_persona.get('tips', [])[:2])}

=== YOUR TASK ===
1. Analyze what this "{field_category}" field needs based on all available context
2. Draft HIGH-QUALITY content using SPECIFIC details from the user's profile AND project context
3. Do NOT use generic placeholders like [YOUR PROJECT] - use actual information from the provided context
4. Match the tone and expectations of {platform_persona['name']} reviewers/judges
5. RESPECT character/word limits strictly if specified

OUTPUT JSON (no markdown code blocks):
{{
  "content": "The actual text to fill in the field - ready to paste, professional quality",
  "reasoning": "Brief explanation of how you used the profile and project context"
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
