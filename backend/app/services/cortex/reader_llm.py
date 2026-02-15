
import structlog
import google.generativeai as genai
from typing import Optional, Dict, Any, List
from app.config import settings
from app.models import OpportunitySchema
from app.utils.json_utils import robust_json_loads
import json
import asyncio
import re
from urllib.parse import urlparse, urljoin

logger = structlog.get_logger()

# Configure Gemini
if settings.gemini_api_key:
    genai.configure(api_key=settings.gemini_api_key)

class ReaderLLM:
    """
    The 'Reader' V2: Turns Raw HTML/Text into Structured JSON.
    UPGRADED: Can extract MULTIPLE opportunities from list pages.
    Optimized for Gemini Flash (Fast/Cheap).
    """
    
    MODEL_NAME = settings.gemini_model or "gemini-1.5-flash"  # Use configured model

    async def parse_opportunity(self, raw_text: str, source_url: str) -> Optional[OpportunitySchema]:
        """
        Extracts a SINGLE opportunity from raw text.
        Use parse_multiple for list pages.
        """
        result = await self.parse_multiple(raw_text, source_url, max_items=1)
        return result[0] if result else None

    async def parse_multiple(
        self, 
        raw_text: str, 
        source_url: str, 
        max_items: int = 50
    ) -> List[OpportunitySchema]:
        """
        V2 CORE: Extracts MULTIPLE opportunities from list/aggregator pages.
        This is critical for DevPost, DoraHacks, etc. that show many items per page.
        """
        if not settings.gemini_api_key:
            logger.warning("Gemini API key not configured")
            return []

        # Truncate text to avoid token limits but be generous for list pages
        truncated_text = raw_text[:80000]
        
        # Detect platform for specialized parsing
        platform_hint = self._detect_platform(source_url)

        prompt = f"""
        You are a Data Extraction Specialist for {platform_hint}.
        
        Extract UP TO {max_items} distinct opportunities (hackathons, scholarships, bounties, grants, competitions) from the page below.
        
        Return a JSON ARRAY. Each item must match this schema:
        {{
            "title": "String (opportunity name)",
            "organization": "String (hosting org/company)",
            "amount": Number (total prize pool in USD - EXTRACT FROM "Prize", "Bounty", "Grant Total", "Award", "Prize Pool" sections. Parse values like '$50,000', '50K USDC', 'Up to $10,000'. Set to 0 ONLY if truly unknown),
            "amount_display": "Human-readable prize string (e.g. '$50,000', 'Up to $10K', '$5K USDC')",
            "deadline": "ISO 8601 Date String (YYYY-MM-DD) or null",
            "deadline_timestamp": Number (Unix Timestamp) or null,
            "geo_tags": ["String"] (e.g. ["Global", "USA", "Remote"]),
            "type_tags": ["String"] (e.g. ["Hackathon", "Bounty", "Grant"]),
            "description": "Short summary (1-2 sentences)",
            "eligibility_text": "Requirements snippet",
            "source_url": "Direct URL to this specific opportunity (if extractable)"
        }}

        Platform-Specific Rules for {platform_hint}:
        - DevPost: Each hackathon card is one opportunity.
        - DoraHacks: Each hackathon or prize-active BUIDL is one opportunity.
        - HackerOne/Intigriti: Each public bug bounty program is one opportunity. Organization is the brand (e.g. 'TikTok', 'Google'). Title is the program name.
        - Superteam/Replit/Algorand: Each bounty/quest listing is one opportunity. Amount is the prize.
        - MLH: Each event card is one opportunity.
        - Bounty platforms: Each bounty listing is one opportunity.
        - Kaggle: Each competition is one opportunity.
        
        General Rules:
        1. If deadline is missing, use null (don't guess).
        2. Geo Tags: "Remote"/"Online" → add "Global". Detect country requirements.
        3. Type Tags: Hackathon, Grant, Bounty, Scholarship, Competition, Internship
        4. If prize is unclear or not explicitly stated as a number, set amount_display to "Check listing for prize pool" and amount to 0. NEVER use "Varies".
        5. Skip expired opportunities if clearly marked as closed/ended.
        6. source_url should be the direct link if visible, else use "{source_url}"
        
        Source Page URL: {source_url}
        
        Page Content:
        {truncated_text}
        
        Return ONLY a valid JSON array. No markdown, no explanations.
        """

        try:
            model = genai.GenerativeModel(self.MODEL_NAME)
            response = await model.generate_content_async(
                prompt, 
                generation_config={"response_mime_type": "application/json"}
            )
            
            # Parse JSON response
            raw_response = response.text.strip()
            
            # Handle potential JSON issues
            if raw_response.startswith("```"):
                raw_response = raw_response.split("```")[1]
                if raw_response.startswith("json"):
                    raw_response = raw_response[4:]
            
            data = robust_json_loads(raw_response)
            
            # Ensure it's a list
            if isinstance(data, dict):
                data = [data]
            
            opportunities = []
            for item in data[:max_items]:
                try:
                    # Generate stable ID
                    item_url = item.get('source_url') or item.get('url') or source_url
                    
                    # NORMALIZE URL to prevent 404s and duplication
                    item_url = self._normalize_url(item_url, source_url)
                    item['source_url'] = item_url
                    
                    from app.services.flink_processor import generate_opportunity_id
                    item['id'] = generate_opportunity_id(item)
                    
                    # Map 'title' to 'name' for schema compatibility
                    if 'title' in item and 'name' not in item:
                        item['name'] = item['title']
                    elif 'name' in item and 'title' not in item:
                        item['title'] = item['name']
                    
                    # Validate with Pydantic
                    opp = OpportunitySchema(**item)
                    opportunities.append(opp)
                    
                except Exception as parse_error:
                    logger.warning(
                        "Failed to parse individual opportunity", 
                        error=str(parse_error),
                        item=str(item)[:100]
                    )
                    continue
            
            logger.info(
                "Reader LLM extraction complete",
                source=source_url[:50],
                extracted=len(opportunities),
                platform=platform_hint
            )
            
            return opportunities

        except json.JSONDecodeError as je:
            logger.error("Reader LLM JSON parse error", url=source_url, error=str(je))
            return []
        except Exception as e:
            logger.error("Reader LLM extraction failed", url=source_url, error=str(e))
            return []

    def _detect_platform(self, url: str) -> str:
        """Detect platform for specialized parsing hints"""
        url_lower = url.lower()
        
        if 'devpost.com' in url_lower:
            return 'DevPost'
        elif 'dorahacks.io' in url_lower:
            return 'DoraHacks'
        elif 'mlh.io' in url_lower:
            return 'Major League Hacking (MLH)'
        elif 'hackquest' in url_lower:
            return 'HackQuest'
        elif 'angelhack' in url_lower:
            return 'AngelHack'
        elif 'devfolio' in url_lower:
            return 'Devfolio'
        elif 'kaggle.com' in url_lower:
            return 'Kaggle'
        elif 'gitcoin' in url_lower:
            return 'Gitcoin'
        elif 'immunefi' in url_lower:
            return 'Immunefi Bug Bounty'
        elif 'hackerone' in url_lower:
            return 'HackerOne Bug Bounty'
        elif 'bugcrowd' in url_lower:
            return 'Bugcrowd Bug Bounty'
        elif 'superteam' in url_lower or 'earn.superteam' in url_lower:
            return 'Superteam (Solana Ecosystem)'
        elif 'layer3' in url_lower:
            return 'Layer3 Web3 Quests'
        elif 'bold.org' in url_lower:
            return 'Bold.org Scholarships'
        elif 'scholarships.com' in url_lower:
            return 'Scholarships.com'
        elif 'fastweb' in url_lower:
            return 'Fastweb Scholarships'
        else:
            return 'General Opportunity Platform'

    def _normalize_url(self, url: str, base_url: str) -> str:
        """
        Normalize URLs to prevent duplicates and broken links.
        Especially handles DevPost, DoraHacks, etc.
        """
        if not url:
            return base_url
            
        try:
            # 1. Resolve relative URLs
            if not url.startswith(('http://', 'https://')):
                url = urljoin(base_url, url)
                
            # 2. Platform specialized normalization
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            path = parsed.path.rstrip('/')
            
            # DevPost Normalization: ALWAYS use canonical path format (devpost.com/hackathons/name)
            # Subdomain URLs (e.g., project.devpost.com) break after hackathons end!
            if 'devpost.com' in domain:
                # 1. Handle subdomains FIRST (e.g., gemini-3-hackathon.devpost.com → devpost.com/hackathons/gemini-3-hackathon)
                if domain != 'devpost.com' and domain.endswith('.devpost.com'):
                    # Extract project name from subdomain
                    project_name = domain.replace('.devpost.com', '')
                    if project_name and project_name not in ['www', 'api', 'help', 'blog', 'info']:
                        return f"https://devpost.com/hackathons/{project_name}/"
                
                # 2. If path is /hackathons/projectName, normalize it
                if path.startswith('/hackathons/'):
                    project_name = path.replace('/hackathons/', '').split('/')[0]
                    # Restore canonical path which is most compatible
                    if project_name and project_name not in ['hackathons', 'challenges', 'discover', '']:
                        return f"https://devpost.com/hackathons/{project_name}/"
                
                # 3. Default: keep as canonical path
                return f"https://devpost.com{path}/" if path else "https://devpost.com/"
            
            # DoraHacks Normalization
            if 'dorahacks.io' in domain:
                # Keep only the main path, strip track IDs etc.
                if path.startswith('/hackathon/'):
                    return f"https://dorahacks.io{path}"
            
            # Generic: Strip common tracking query params
            query_to_strip = ['ref', 'utm_source', 'utm_medium', 'utm_campaign', 'ref_feature', 'ref_medium']
            from urllib.parse import parse_qs, urlencode, urlunparse
            query_params = parse_qs(parsed.query)
            filtered_params = {k: v for k, v in query_params.items() if k.lower() not in query_to_strip}
            
            new_query = urlencode(filtered_params, doseq=True)
            return urlunparse(parsed._replace(query=new_query, fragment=''))
            
        except Exception as e:
            logger.warning("URL normalization failed", url=url, error=str(e))
            return url


reader_llm = ReaderLLM()
