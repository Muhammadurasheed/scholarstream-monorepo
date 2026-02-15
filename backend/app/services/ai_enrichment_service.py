"""
AI Enrichment Service (Consolidated V2)
Batch enrichment of opportunities using Gemini with specialized platform rules.
"""
import google.generativeai as genai
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import asyncio
import structlog
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from app.config import settings
from app.utils.json_utils import robust_json_loads

logger = structlog.get_logger()

class AIEnrichmentService:
    """
    Enriches raw opportunity data using Gemini AI.
    Optimized for high-density discovery from specific hubs (HackerOne, Superteam, etc.)
    """
    
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model)
        self.batch_size = 10 
    
    def clean_html(self, html_content: str) -> str:
        """Aggressively clean HTML to reduce token usage"""
        if not html_content: return ""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Decompose heavy tags, but PRESERVE hydration JSON for SPAs.
            # Many of our targets (DoraHacks, HackQuest, TAIKAI, Superteam) are Next.js/SPAs where
            # the opportunity data lives inside <script id="__NEXT_DATA__" type="application/json">...</script>.
            # If we delete all scripts we destroy the only structured data on the page.
            for tag in soup(['style', 'svg', 'path', 'noscript', 'meta', 'link', 'iframe', 'footer', 'nav']):
                tag.decompose()

            # Remove scripts except allowlisted ones (__NEXT_DATA__, ld+json, and common SPA hydration blobs)
            for script in soup.find_all('script'):
                sid = (script.get('id') or '').strip()
                stype = (script.get('type') or '').strip().lower()
                keep = False

                if sid == '__NEXT_DATA__':
                    keep = True
                elif stype in ['application/ld+json', 'application/json']:
                    # Some sites embed structured data as JSON-LD or app state as application/json.
                    keep = True
                else:
                    # Nuxt hydration (common fallback)
                    text = (script.string or '')
                    if 'window.__NUXT__' in text or '__NUXT__' in text:
                        keep = True

                if not keep:
                    script.decompose()

            body = soup.body
            cleaned = str(body)[:60000] if body else str(soup)[:60000]

            # Diagnostic: Log content density
            if len(cleaned) < 500:
                logger.info("Content density low", length=len(cleaned), url=getattr(self, '_last_url', 'unknown'))

            return cleaned
        except Exception as e:
            logger.warning("HTML Clean failed", error=str(e))
            return html_content[:60000]

    async def extract_opportunities_from_html_batch(self, items: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Batch process multiple HTML pages with platform-specific context"""
        if not items: return []
            
        cleaned_items = []
        for item in items:
            self._last_url = item.get('url') # For logging context
            clean = self.clean_html(item.get('html', ''))
            if len(clean) > 50: # Lowered threshold for lean SPA cards
                cleaned_items.append({'url': item.get('url'), 'content': clean})
        
        if not cleaned_items:
            logger.warning("Batch processing aborted: No valid content found", total_items=len(items))
            return []

        context_str = ""
        for i, item in enumerate(cleaned_items):
            context_str += f"\n\n=== START PAGE {i+1} URL: {item['url']} ===\n{item['content']}\n=== END PAGE {i+1} ===\n"

        prompt = f"""
You are a high-speed financial discovery engine. 
Extract EVERY distinct opportunity (Scholarship, Grant, Hackathon, Bounty) from the provided HTML.
Combined JSON list of objects: title, organization, amount_value (int), amount_display, deadline (YYYY-MM-DD), description, url (absolute), type, eligibility.

Rules:
- HackerOne: Each bug bounty program is one opportunity.
- DoraHacks/Superteam/HackQuest/TAIKAI: Each bounty, prize, or hackathon is one opportunity.
- DevPost: Use canonical devpost.com/hackathons/projectName/ format only.
- If no opportunities found, return [].

DATA:
{context_str}

RETURN JSON ARRAY ONLY.
"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Diagnostic: Log prompt size
                logger.info("Sending Discovery Mission to Gemini", 
                            page_count=len(cleaned_items), 
                            payload_size=len(context_str),
                            attempt=attempt+1)
                            
                response = await self.model.generate_content_async(prompt)
                text = response.text.strip()
                
                # Diagnostic: Log response size
                logger.info("Gemini Analysis Received", response_size=len(text))
                
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                    
                extracted = robust_json_loads(text)
                if not isinstance(extracted, (list, dict)): return []
                if isinstance(extracted, dict): extracted = [extracted]
                
                valid_opportunities = []
                for item in extracted:
                    try:
                        if not item.get('title') or not item.get('url'): continue
                        
                        # Apply URL Normalization & Fix DevPost 404s
                        item['url'] = self._normalize_url(item['url'])
                        
                        # CRITICAL FIX: Map amount_value → amount (the field the model expects)
                        if item.get('amount_value') is not None:
                            item['amount'] = float(item.get('amount_value', 0))
                        elif item.get('amount') is None:
                            item['amount'] = 0.0
                        
                        # Generate amount_display if missing
                        if not item.get('amount_display') and item.get('amount'):
                            item['amount_display'] = f"${item['amount']:,.0f}"
                        
                        if not item.get('eligibility'): item['eligibility'] = "Open to all users."
                        if item.get('deadline') in ["Unknown", "TBD", "None"]: item['deadline'] = None

                        valid_opportunities.append(item)
                    except Exception: continue

                logger.info("Batch extraction complete", total_found=len(valid_opportunities), attempt=attempt+1)
                return valid_opportunities

            except Exception as e:
                if any(x in str(e) for x in ["429", "RESOURCE_EXHAUSTED"]):
                    await asyncio.sleep(20 * (attempt + 1))
                    continue
                logger.error("Batch Extraction failed", error=str(e)[:500])
                return []
        return []

    def _normalize_url(self, url: str) -> str:
        """Surgical URL stability layer"""
        if not url: return url
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            path = parsed.path.rstrip('/')
            
            # CRITICAL FIX: DevPost subdomain URLs are CORRECT and should NOT be modified
            # The API returns https://slug.devpost.com/ which is the permanent, working format
            # Converting to devpost.com/hackathons/slug CAUSES 404 ERRORS
            # Previous logic was DESTROYING working URLs
            
            # DevPost: Keep subdomain URLs unchanged - they are already correct
            if 'devpost.com' in domain:
                # Just return the URL as-is - subdomain format is correct
                return url
            
            # DoraHacks / HackQuest consistency
            if 'dorahacks.io' in domain or 'hackquest.io' in domain:
                return f"https://{domain}{path}/"

            return url
        except Exception: return url

    async def enrich_opportunities_batch(self, raw_opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Legacy fallback/enrichment for pre-scraped items"""
        logger.info("Starting enrichment batch", total=len(raw_opportunities))
        # Logic matches extract_opportunities_from_html_batch but for structured JSON inputs
        return raw_opportunities # Simplified for now as discovery-driven extraction is preferred

    async def extract_opportunities_from_html(self, html_content: str, url: str) -> List[Dict[str, Any]]:
        """Single page extraction wrapper"""
        return await self.extract_opportunities_from_html_batch([{'url': url, 'html': html_content}])

# Global instance
ai_enrichment_service = AIEnrichmentService()
