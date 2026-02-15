"""
Chrome Extension API Endpoints
Provides user profile data and AI-powered form field mapping
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Dict, List, Any, Optional
import structlog
import json
from pydantic import BaseModel

from app.database import get_user_profile
from app.services.ai_service import ai_service
from firebase_admin import auth

router = APIRouter(prefix="/api/extension", tags=["extension"])
logger = structlog.get_logger()


class FormField(BaseModel):
    """Form field structure detected by extension"""
    id: str
    name: str
    type: str
    selector: str
    label: str
    placeholder: str
    required: bool


class FieldMappingRequest(BaseModel):
    """Request body for form field mapping"""
    form_fields: List[Dict[str, Any]]
    user_profile: Dict[str, Any]
    project_context: Optional[str] = None
    target_field: Optional[Dict[str, Any]] = None
    instruction: Optional[str] = None


async def verify_token(authorization: str) -> str:
    """Verify Firebase token from Authorization header"""
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.split('Bearer ')[1]
    
    # Production Security: No Test Tokens allowed
    if token == 'TEST_TOKEN' or 'TEST_TOKEN' in token:
        logger.warning("Blocked attempt to use TEST_TOKEN in production")
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token['uid']
    except Exception as e:
        logger.error("Token verification failed", error=str(e))
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@router.get("/user-profile")
async def get_extension_user_profile(authorization: Optional[str] = Header(None)):
    """
    Get comprehensive user profile for form auto-fill

    Returns all user data needed for filling scholarship applications:
    - Personal information
    - Academic details
    - Contact information
    - Saved essay snippets
    """
    user_id = await verify_token(authorization)

    # MOCK PROFILE FOR DEV/TEST MODE
    # Production Mode: Only fetch real profiles
    if user_id == "test_user_123":
        raise HTTPException(status_code=403, detail="Test accounts disabled")

    try:
        profile = await get_user_profile(user_id)

        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")

        extension_profile = {
            'full_name': profile.get('name', ''),
            'first_name': profile.get('name', '').split()[0] if profile.get('name') else '',
            'last_name': ' '.join(profile.get('name', '').split()[1:]) if profile.get('name') else '',
            'email': profile.get('email', ''),
            'phone': profile.get('phone', ''),
            'date_of_birth': profile.get('date_of_birth', ''),
            'address': {
                'street': profile.get('address', {}).get('street', ''),
                'city': profile.get('city', ''),
                'state': profile.get('state', ''),
                'zip_code': profile.get('zip_code', ''),
                'country': profile.get('country', '')
            },
            'academic': {
                'school_name': profile.get('school', ''),
                'academic_status': profile.get('academic_status', ''),
                'grade_level': profile.get('year', ''),
                'major': profile.get('major', ''),
                'gpa': profile.get('gpa', ''),
                'graduation_year': profile.get('graduation_year', ''),
                'expected_graduation': profile.get('graduation_year', '')
            },
            'demographics': {
                'gender': profile.get('gender', ''),
                'ethnicity': profile.get('ethnicity', ''),
                'citizenship': profile.get('citizenship', ''),
                'first_generation': profile.get('background', []).count('First-generation') > 0,
                'military_affiliation': profile.get('military_affiliation', False)
            },
            'interests': profile.get('interests', []),
            'skills': profile.get('skills', []),
            'extracurriculars': profile.get('extracurriculars', []),
            'work_experience': profile.get('work_experience', []),
            'essays': {
                'personal_statement': profile.get('essays', {}).get('personal_statement', ''),
                'career_goals': profile.get('essays', {}).get('career_goals', ''),
                'community_impact': profile.get('essays', {}).get('community_impact', ''),
                'why_this_scholarship': profile.get('essays', {}).get('why_this_scholarship', '')
            },
            'social_media': {
                'linkedin': profile.get('linkedin_url', ''),
                'github': profile.get('github_url', ''),
                'portfolio': profile.get('portfolio_url', ''),
                'twitter': profile.get('twitter_handle', '')
            },
            # DEEP PROFILE / DIGITAL DNA
            'bio': profile.get('bio', ''),
            'professional_summary': profile.get('bio', ''), # Alias
            'hard_skills': profile.get('hard_skills', []),
            'soft_skills': profile.get('soft_skills', []),
            'projects': profile.get('projects', []), # Rich Project Context
            'experience': profile.get('experience', []) # Work Experience
        }

        logger.info("Profile fetched for extension", user_id=user_id)

        return {
            'success': True,
            'profile': extension_profile
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch extension profile", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch profile: {str(e)}")


@router.post("/map-fields")
async def map_form_fields(
    request: FieldMappingRequest,
    authorization: Optional[str] = Header(None)
):
    """
    AI-powered form field mapping

    Uses Gemini to intelligently map form fields to user profile data
    Returns a dictionary mapping field selectors to suggested values

    Example response:
    {
        "field_mappings": {
            "#firstName": "John",
            "#lastName": "Doe",
            "#email": "john@example.com",
            "#gpa": "3.8"
        }
    }
    """
    user_id = await verify_token(authorization)

    try:
        form_fields = request.form_fields
        user_profile = request.user_profile
        project_context = request.project_context

        # FOCUS FILL MODE: If a specific target field is provided, generate content for it
        if request.target_field:
            logger.info(f"✨ FOCUS FILL (Sparkle): Delegating to Copilot Service for '{request.target_field.get('name')}'")
            
            from app.services.copilot_service import copilot_service
            
            # Pass project_context and instruction to generate_field_content
            result = await copilot_service.generate_field_content(
                target_field=request.target_field,
                user_profile=user_profile,
                instruction=request.instruction,
                page_url=request.target_field.get('pageUrl', ''),
                project_context=project_context  # Now passing project context!
            )
            
            return {
                "field_mappings": {},
                "sparkle_result": {
                    "content": result['content'],
                    "reasoning": result['reasoning']
                }
            }
            
        # BATCH MAPPING MODE: Map all fields (Fallback or "Fill All" button)
        logger.info(
            "Mapping form fields",
            user_id=user_id,
            field_count=len(form_fields)
        )

        prompt = f"""
You are an expert AI form-filler for the ScholarStream extension.
Your goal is to fill as many fields as possible to save the user time.

USER PROFILE:
{json.dumps(user_profile, indent=2)}

PROJECT CONTEXT (Uploaded Document):
{project_context if project_context else "No project context provided."}

FORM FIELDS DETECTED:
{json.dumps(form_fields, indent=2)}

INSTRUCTIONS:
1. Analyze the "label", "name", "placeholder", and "id" of each field.
2. Map it to the most relevant data from the USER PROFILE or PROJECT CONTEXT.
3. **CRITICAL**: If a field asks for "Elevator Pitch", "Description", or "Inspiration", use the PROJECT CONTEXT to write a specific, high-quality answer. Do NOT use generic placeholders like "[Problem]". Fill it with actual details from the uploaded doc.
4. For "Skills" or "Interests", join the list with commas.
5. For URL fields (LinkedIn, GitHub), the VALUE should be the URL, NOT the selector.

**CRITICAL SELECTOR RULES**:
- The "selector" in your output MUST be the EXACT "selector" value from the FORM FIELDS DETECTED input above.
- Selectors look like: "#firstName", "[name='email']", "textarea", etc.
- Selectors are CSS selectors, NOT URLs. Never use a URL as a selector key.
- If a field has selector "#linkedin", the key should be "#linkedin" and the VALUE should be the URL.

OUTPUT FORMAT:
Return a valid JSON object containing ONLY the mappings.
Keys must be CSS selectors from the input. Values are what to fill in those fields.
{{
    "field_mappings": {{
        "#fieldId": "value_to_fill",
        "[name='email']": "user@example.com"
    }}
}}
"""

        result = await ai_service.generate_content_async(prompt)

        import re
        
        # 1. Improved JSON Extraction
        text = result.strip()
        # Regex to find the first JSON object block
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            text = json_match.group(0)
        elif '```json' in text:
            # Fallback for code blocks if regex somehow misses
            text = text.split('```json')[1].split('```')[0].strip()
        
        try:
            mapping_response = json.loads(text)
        except json.JSONDecodeError:
            # Last ditch effort: try to fix common JSON errors (optional, kept simple for now)
            logger.warning("JSON decode failed, attempting to parse raw text", text_preview=text[:100])
            raise

        field_mappings = mapping_response.get('field_mappings', {})

        logger.info(
            "Field mapping complete",
            user_id=user_id,
            mapped_count=len(field_mappings)
        )

        return {
            'success': True,
            'field_mappings': field_mappings,
            'mapped_count': len(field_mappings),
            'total_fields': len(form_fields)
        }

    except json.JSONDecodeError as e:
        logger.error("Failed to parse AI response", error=str(e))
        raise HTTPException(status_code=500, detail="AI response parsing failed")

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower() or "exhausted" in error_msg.lower():
            logger.warning("Gemini rate limit hit during field mapping", error=error_msg)
            raise HTTPException(status_code=429, detail="AI service temporarily unavailable. Please try again in a moment.")
        logger.error("Field mapping failed", user_id=user_id, error=error_msg)
        raise HTTPException(status_code=500, detail=f"Field mapping failed: {error_msg}")


@router.post("/save-application-data")
async def save_application_data(
    data: Dict[str, Any],
    authorization: Optional[str] = Header(None)
):
    """
    Save application data from extension for future reuse

    Allows extension to persist filled form data for similar applications
    """
    user_id = await verify_token(authorization)

    try:
        from app.database import db

        application_ref = db.collection('extension_saved_data').document(user_id)

        saved_data = application_ref.get().to_dict() or {}

        if 'applications' not in saved_data:
            saved_data['applications'] = []

        saved_data['applications'].append({
            'url': data.get('url', ''),
            'platform': data.get('platform', ''),
            'form_data': data.get('form_data', {}),
            'saved_at': data.get('timestamp')
        })

        if len(saved_data['applications']) > 50:
            saved_data['applications'] = saved_data['applications'][-50:]

        application_ref.set(saved_data, merge=True)

        logger.info("Application data saved", user_id=user_id)

        return {
            'success': True,
            'message': 'Application data saved successfully'
        }

    except Exception as e:
        logger.error("Failed to save application data", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to save data: {str(e)}")

class ChatRequest(BaseModel):
    query: str
    page_context: Dict[str, Any]
    project_context: Optional[str] = None
    # FAANG-level KB control: track which docs are explicitly mentioned
    mentioned_docs: Optional[List[str]] = None  
    # Toggle: should profile be included in knowledge base?
    include_profile: bool = True

@router.post("/chat")
async def copilot_chat(
    request: ChatRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Co-Pilot Chat Endpoint V2
    Handles multimodal RAG chat with FAANG-level knowledge base control.
    
    Key Features:
    - mentioned_docs: Only use explicitly @mentioned documents
    - include_profile: Toggle to exclude user profile from KB
    """
    user_id = await verify_token(authorization)
    
    try:
        from app.services.copilot_service import copilot_service
        
        # FAANG-level KB control: Only fetch profile if include_profile is True
        user_profile = None
        if request.include_profile:
            try:
                profile_response = await get_extension_user_profile(authorization)
                user_profile = profile_response.get('profile')
            except Exception as profile_err:
                logger.warning("Profile fetch failed, proceeding without profile", error=str(profile_err))
        
        logger.info(
            "Copilot chat with KB controls",
            user_id=user_id,
            include_profile=request.include_profile,
            mentioned_docs=request.mentioned_docs,
            has_project_context=bool(request.project_context)
        )
        
        response = await copilot_service.chat(
            query=request.query,
            page_context=request.page_context,
            project_context=request.project_context,
            user_profile=user_profile,
            mentioned_docs=request.mentioned_docs,
            include_profile=request.include_profile
        )
        
        return {
            "success": True,
            "data": response
        }
        
    except Exception as e:
        logger.error("Chat endpoint failed", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
