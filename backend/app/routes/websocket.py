"""
WebSocket Endpoint for Real-Time Opportunity Streaming
Consumes enriched opportunities from EventBroker and pushes matches to connected clients
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from typing import Dict, List, Optional, Any
import json
import asyncio
import structlog

from firebase_admin import auth
from datetime import datetime

from app.database import get_user_profile, FirebaseDB
from app.services.personalization_engine import PersonalizationEngine

from app.models import (
    Scholarship, ScholarshipEligibility, ScholarshipRequirements
)

router = APIRouter()
logger = structlog.get_logger()


class ConnectionManager:
    """Manages WebSocket connections and routes messages to appropriate users"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_profiles: Dict[str, Dict] = {}

    async def connect(self, user_id: str, websocket: WebSocket, user_profile: Dict):
        """Register new WebSocket connection"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_profiles[user_id] = user_profile

        logger.info(
            "WebSocket connected",
            user_id=user_id,
            total_connections=len(self.active_connections)
        )

    def disconnect(self, user_id: str):
        """Remove WebSocket connection"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.user_profiles:
            del self.user_profiles[user_id]

        logger.info(
            "WebSocket disconnected",
            user_id=user_id,
            remaining_connections=len(self.active_connections)
        )

    async def send_personal_message(self, user_id: str, message: Dict):
        """Send message to specific user"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
                logger.debug("Message sent to user", user_id=user_id)
            except Exception as e:
                logger.error(
                    "Failed to send message",
                    user_id=user_id,
                    error=str(e)
                )
                self.disconnect(user_id)

    async def broadcast(self, message: Dict, exclude_user: Optional[str] = None):
        """Broadcast message to all connected clients"""
        disconnected_users = []

        for user_id, connection in self.active_connections.items():
            if user_id == exclude_user:
                continue

            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(
                    "Failed to broadcast to user",
                    user_id=user_id,
                    error=str(e)
                )
                disconnected_users.append(user_id)

        for user_id in disconnected_users:
            self.disconnect(user_id)

    def get_all_user_ids(self) -> List[str]:
        """Get list of all connected user IDs"""
        return list(self.active_connections.keys())


manager = ConnectionManager()
personalization_engine = PersonalizationEngine()
firebase_db = FirebaseDB()  # For persisting opportunities to Firestore


async def verify_firebase_token(token: str) -> Optional[str]:
    """Verify Firebase ID token and return user ID"""
    # Production Security: Verify against Firebase
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token['uid']
    except Exception as e:
        logger.error("Token verification failed", error=str(e))
        return None


async def process_and_route_opportunity(final_data: Dict):
    """
    Process enriched opportunity and route to connected clients.
    Moved out of consume_kafka_stream for reuse.
    """
    try:
        # Convert to Scholarship Model
        scholarship = convert_to_scholarship(final_data)

        if not scholarship:
            return

        # Start Personalization Engine (scoring)
        # We need to fetch all active user profiles to match against
        active_user_ids = manager.get_all_user_ids()

        if not active_user_ids:
            logger.info("No active users to match against", opportunity=scholarship.title)
            return

        # Persist to Firestore (Source of Truth)
        # Note: Refinery already does a fallback save, but we save here to be sure
        # if the flow came from a different source.
        # await firebase_db.save_scholarship(scholarship) 

        # Match against active users
        match_count = 0
        for user_id in active_user_ids:
            user_profile_data = manager.user_profiles.get(user_id)
            if not user_profile_data:
                continue

            # Calculate Match Score
            score = personalization_engine.calculate_match_score(scholarship, user_profile_data)

            if score.score >= 0.6: # configurable threshold
                # Send "New Opportunity" Notification
                await manager.send_personal_message(user_id, {
                    'type': 'new_opportunity_match',
                    'opportunity': scholarship.model_dump(),
                    'score': score.score,
                    'reasons': score.match_reasons,
                    'timestamp': datetime.utcnow().isoformat()
                })
                match_count += 1
                
                # Persist match to user's history
                await firebase_db.add_user_match(user_id, scholarship.id)

        logger.info(
            "Opportunity routed",
            title=scholarship.title,
            matched_users=match_count,
            total_active=len(active_user_ids)
        )

    except Exception as e:
        logger.error("Routing failed", error=str(e))


async def subscribe_to_opportunities():
    """
    Subscribe to the EventBroker for enriched opportunities.
    This replaces the Kafka consumer loop.
    """
    from app.main import broker
    from app.config import settings

    async def handle_opportunity(payload: Dict[str, Any]):
        try:
            # MemoryBroker passes the unwrapped payload directly (not {key, payload} envelope)
            if not payload:
                return
            
            # Unwrap if needed (Refinery sends model_dump())
            await process_and_route_opportunity(payload)
            
        except Exception as e:
            logger.error("WebSocket handler failed", error=str(e))

    await broker.subscribe(settings.topic_enriched_opportunity, handle_opportunity)
    logger.info("WebSocket Service subscribed to EventBroker", topic=settings.topic_enriched_opportunity)


def normalize_opportunity(data: Any) -> Dict:
    """
    SELF-HEALING MECHANISM
    Ensures data conforms to OpportunitySchema before strict validation.
    Fixes:
    - Missing 'name' (maps from 'title')
    - Missing 'description' (defaults to tagline or generic text)
    - Missing 'id' (generates hash)
    """
    if not isinstance(data, dict):
        return {}

    # 1. Heal Name (Critical)
    if 'name' not in data and 'title' in data:
        data['name'] = data['title']
    
    # 2. Heal Description
    if not data.get('description'):
        # Construct a decent description from other fields if missing
        parts = []
        if data.get('tagline'):
            parts.append(data['tagline'])
        
        parts.append(f"Organization: {data.get('organization', 'Unknown')}")
        
        if data.get('deadline'):
            parts.append(f"Deadline: {data['deadline']}")
            
        data['description'] = " | ".join(parts) if parts else "No detailed description available."

    # 3. Heal Tags (Ensure List[str])
    if 'tags' in data:
        tags = data['tags']
        if isinstance(tags, list):
            # Flatten dict tags like [{'id':1, 'name':'foo'}] -> ['foo']
            clean_tags = []
            for t in tags:
                if isinstance(t, dict):
                    clean_tags.append(t.get('name', ''))
                elif isinstance(t, str):
                    clean_tags.append(t)
            data['tags'] = clean_tags

    # 4. Heal ID (content hash)
    if not data.get('id'):
         import hashlib
         # Generate ID from URL (preferred) or Title
         id_source = data.get('url') or data.get('source_url') or data.get('name') or "unknown"
         hash_object = hashlib.md5(id_source.encode())
         data['id'] = f"gen_{hash_object.hexdigest()}"

    return data


def convert_to_scholarship(enriched_data: Dict) -> Optional[Scholarship]:
    """
    Convert enriched opportunity dict from Kafka to Scholarship model
    for Firestore persistence. STRICT VALIDATION APPLIED.
    """
    try:
        # DEFENSIVE: Ensure input is a dictionary
        if not isinstance(enriched_data, dict):
            logger.error("convert_to_scholarship received non-dict", type=type(enriched_data).__name__, preview=str(enriched_data)[:100])
            return None

        # --- STRICT VALIDATION: FILTER OUT JUNK ---
        # 1. Check for error flags from the enrichment layer (e.g., reCAPTCHA blocks)
        if enriched_data.get('error'):
            logger.warning("Dropped opportunity: Contains error flag", error_msg=enriched_data.get('error'))
            return None

        # 2. Check for missing critical fields
        name = enriched_data.get('name') or enriched_data.get('title')
        url = enriched_data.get('url') or enriched_data.get('source_url')
        
        if not name or (name and name.lower() in ['unknown', 'unknown opportunity', 'none']):
            logger.warning("Dropped opportunity: Invalid name", data_preview=str(enriched_data)[:100])
            return None
            
        if not url:
             logger.warning("Dropped opportunity: Missing URL", name=name)
             return None

        # 3. Check for obvious scraper failure signatures (e.g. login pages, captchas)
        # Fix: Handle explicit None in description
        description = (enriched_data.get('description') or '').lower()
        if any(bad_term in description for bad_term in ['captcha', 'please verify', 'access denied', 'turn on javascript']):
             logger.warning("Dropped opportunity: Description indicates scraper block", name=name)
             return None
        # ------------------------------------------

        now = datetime.utcnow().isoformat()
        
        # Parse eligibility (may be dict or missing)
        eligibility_data = enriched_data.get('eligibility', {})
        if isinstance(eligibility_data, dict):
            eligibility = ScholarshipEligibility(**eligibility_data)
        else:
            # If it's a string or other type, try to coerce or default
            eligibility = ScholarshipEligibility(description=str(eligibility_data)) if eligibility_data else ScholarshipEligibility()
        
        # Parse requirements (may be dict or missing)
        requirements_data = enriched_data.get('requirements', {})
        if isinstance(requirements_data, dict):
            requirements = ScholarshipRequirements(**requirements_data)
        else:
             requirements = ScholarshipRequirements(description=str(requirements_data)) if requirements_data else ScholarshipRequirements()
        
        # Build Scholarship model with defaults for missing fields
        # MAPPING: OpportunitySchema (Refinery) -> Scholarship (Frontend)
        geo_tags = enriched_data.get('geo_tags', [])
        type_tags = enriched_data.get('type_tags', [])
        all_tags = list(set(enriched_data.get('tags', []) + geo_tags + type_tags))

        # Calculate deadline_timestamp
        deadline_str = enriched_data.get('deadline') or now
        try:
            # Try parsing simple YYYY-MM-DD
            if len(deadline_str) == 10:
                dt = datetime.strptime(deadline_str, "%Y-%m-%d")
            else:
                dt = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
            deadline_timestamp = int(dt.timestamp())
        except Exception:
            # Fallback to now + 30 days if parse fails
            deadline_timestamp = int(datetime.utcnow().timestamp()) + (30 * 24 * 3600)

        # Create Deterministic ID if missing
        opp_id = enriched_data.get('id')
        if not opp_id:
            import hashlib
            # Generate ID from URL (preferred) or Title
            id_source = url or name or str(datetime.utcnow().timestamp())
            hash_object = hashlib.md5(id_source.encode())
            opp_id = f"gen_{hash_object.hexdigest()}"

        scholarship = Scholarship(
            id=opp_id,
            name=name, # REQUIRED FIELD
            title=name, # Optional/Legacy
            organization=enriched_data.get('organization', 'Unknown Organization'),
            amount=float(enriched_data.get('amount', 0) or 0),
            amount_display=enriched_data.get('amount_display') or f"${enriched_data.get('amount', 0):,.0f}",
            deadline=deadline_str,
            deadline_timestamp=deadline_timestamp, # Required Field
            geo_tags=geo_tags,
            type_tags=type_tags,
            description=enriched_data.get('description') or 'No description provided.',
            source_url=url,
            # Optional fields
            eligibility_text=str(enriched_data.get('eligibility', '')) if 'eligibility' in enriched_data else None,
            match_score=float(enriched_data.get('match_score', 0) or 0),
            # Extra fields like 'eligibility' dict will be ignored by Pydantic if extra='ignore'
            # But we map what we can to OpportunitySchema
        )
        return scholarship
    except Exception as e:
        logger.error("Failed to convert enriched data to Scholarship", error=str(e), data_preview=str(enriched_data)[:200])
        return None


async def process_and_route_opportunity(enriched_opportunity: Dict):
    """
    1. Persist enriched opportunity to Firestore
    2. Match against all connected users
    3. Send to users with match score > 60
    """
    # STEP 1: Persist to Firestore (critical for /api/scholarships/matched)
    try:
        scholarship = convert_to_scholarship(enriched_opportunity)
        if scholarship:
            await firebase_db.save_scholarship(scholarship)
            logger.info(
                "Opportunity persisted to Firestore",
                scholarship_id=scholarship.id,
                name=scholarship.title
            )
    except Exception as e:
        logger.error("Failed to persist opportunity to Firestore", error=str(e))
        # Continue with routing even if persistence fails
    
    # STEP 2: Route to connected users
    connected_users = manager.get_all_user_ids()

    if not connected_users:
        logger.debug("No connected users - skipping routing")
        return

    logger.info(
        "Routing opportunity to connected users",
        opportunity_name=enriched_opportunity.get('name'),
        connected_users=len(connected_users)
    )

    for user_id in connected_users:
        user_profile = manager.user_profiles.get(user_id)

        if not user_profile or not isinstance(user_profile, dict):
            logger.warning("Invalid or missing user profile in cache", user_id=user_id)
            continue

        try:
            match_score = calculate_match_score(enriched_opportunity, user_profile)

            if match_score >= 60:
                enriched_opportunity_with_score = enriched_opportunity.copy()
                enriched_opportunity_with_score['match_score'] = match_score
                enriched_opportunity_with_score['match_tier'] = get_match_tier(match_score)
                enriched_opportunity_with_score['priority_level'] = get_priority_level(
                    enriched_opportunity,
                    match_score
                )

                await manager.send_personal_message(
                    user_id=user_id,
                    message={
                        'type': 'new_opportunity',
                        'opportunity': enriched_opportunity_with_score,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )

                # STEP 3: Persist match so it doesn't vanish on refresh
                if scholarship:
                    await firebase_db.add_user_match(user_id, scholarship.id)

                logger.info(
                    "Opportunity pushed to user",
                    user_id=user_id,
                    opportunity_name=enriched_opportunity.get('name'),
                    match_score=match_score
                )
        except Exception as e:
            logger.error(
                "CRITICAL: Match calculation failed", 
                user_id=user_id, 
                profile_type=type(user_profile).__name__,
                profile_preview=str(user_profile)[:100],
                error=str(e),
                traceback=True
            )
            continue


def calculate_match_score(opportunity: Dict, user_profile: Dict) -> float:
    """
    Calculate match score between opportunity and user profile
    Uses PersonalizationEngine logic
    """
    return personalization_engine.calculate_personalized_score(opportunity, user_profile)


def get_match_tier(score: float) -> str:
    """Convert match score to tier"""
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Fair"
    else:
        return "Poor"


def get_priority_level(opportunity: Dict, match_score: float) -> str:
    """Determine priority level based on urgency and score"""
    urgency = opportunity.get('urgency', 'future')

    if urgency == 'immediate':
        return "URGENT"
    elif match_score >= 85:
        return "HIGH"
    elif match_score >= 60:
        return "MEDIUM"
    else:
        return "LOW"


@router.websocket("/ws/opportunities")
async def websocket_endpoint(websocket: WebSocket, token: str = ""):
    """
    WebSocket endpoint for real-time opportunity streaming

    Query params:
        token: Firebase ID token for authentication

    Message types sent to client:
        - connection_established: Sent immediately after connection
        - new_opportunity: Real-time opportunity match
        - heartbeat: Keep-alive ping every 30 seconds
    """
    # CRITICAL: Accept WebSocket connection FIRST before any validation
    # This prevents 403 errors during handshake
    await websocket.accept()
    
    # Now verify the token after connection is established
    if not token:
        await websocket.send_json({
            'type': 'error',
            'message': 'Authentication token required',
            'code': 'AUTH_REQUIRED'
        })
        await websocket.close(code=1008, reason="Authentication token required")
        return
    
    user_id = await verify_firebase_token(token)

    if not user_id:
        await websocket.send_json({
            'type': 'error',
            'message': 'Invalid authentication token',
            'code': 'AUTH_FAILED'
        })
        await websocket.close(code=1008, reason="Invalid authentication token")
        return

    # Production: Always fetch real profile
    user_profile = await get_user_profile(user_id)

    if not user_profile:
        await websocket.send_json({
            'type': 'error',
            'message': 'User profile not found. Please complete onboarding.',
            'code': 'PROFILE_NOT_FOUND'
        })
        await websocket.close(code=1008, reason="User profile not found")
        return

    # Register connection (don't call accept again - already accepted above)
    manager.active_connections[user_id] = websocket
    manager.user_profiles[user_id] = user_profile
    logger.info(
        "WebSocket connected",
        user_id=user_id,
        total_connections=len(manager.active_connections)
    )

    # Client may disconnect immediately after handshake; don't crash the server.
    try:
        await websocket.send_json({
            'type': 'connection_established',
            'message': 'Connected to real-time opportunity stream',
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat()
        })
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        logger.info("Client disconnected before init message", user_id=user_id)
        return

    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)

                message = json.loads(data)
                message_type = message.get('type')

                if message_type == 'ping':
                    try:
                        await websocket.send_json({
                            'type': 'pong',
                            'timestamp': datetime.utcnow().isoformat()
                        })
                    except WebSocketDisconnect:
                        break

                elif message_type == 'update_profile':
                    updated_profile = message.get('profile', {})
                    if isinstance(updated_profile, dict):
                        manager.user_profiles[user_id] = updated_profile
                        logger.info("User profile updated in WebSocket", user_id=user_id)
                    else:
                        logger.warning(
                            "Invalid profile update format",
                            user_id=user_id,
                            received_type=type(updated_profile).__name__
                        )

            except asyncio.TimeoutError:
                # Heartbeats are best-effort; if client is gone, just exit.
                try:
                    await websocket.send_json({
                        'type': 'heartbeat',
                        'timestamp': datetime.utcnow().isoformat()
                    })
                except WebSocketDisconnect:
                    break

            except WebSocketDisconnect:
                break

    except Exception as e:
        logger.error("WebSocket error", user_id=user_id, error=str(e))

    finally:
        manager.disconnect(user_id)
        logger.info("WebSocket cleaned up", user_id=user_id)




# Background task starter removed (Legacy Kafka)

