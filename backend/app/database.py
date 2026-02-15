"""
Firebase Firestore database layer
Handles all database operations with proper error handling
"""
import firebase_admin
from firebase_admin import credentials, firestore
from typing import Optional, List, Dict, Any
from datetime import datetime
import structlog

from app.config import settings
from app.models import Scholarship, UserProfile

logger = structlog.get_logger()


class FirebaseDB:
    """Firebase Firestore database manager"""
    
    def __init__(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if already initialized
            firebase_admin.get_app()
            logger.info("Firebase already initialized")
        except ValueError:
            # Initialize Firebase
            cred = credentials.Certificate(settings.firebase_credentials)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized successfully")
        
        self.db = firestore.client()
    
    # User Profile Operations
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch user profile from Firestore"""
        try:
            doc_ref = self.db.collection('users').document(user_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            logger.error("Failed to fetch user profile", user_id=user_id, error=str(e))
            raise
    
    async def update_user_profile(self, user_id: str, profile: UserProfile) -> bool:
        """Update user profile in Firestore"""
        try:
            doc_ref = self.db.collection('users').document(user_id)
            doc_ref.update({
                'profile': profile.model_dump(),
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            logger.info("User profile updated", user_id=user_id)
            return True
        except Exception as e:
            logger.error("Failed to update user profile", user_id=user_id, error=str(e))
            raise

    async def update_user_last_match_time(self, user_id: str, timestamp: float) -> bool:
        """Update last_match_at in user profile for staleness tracking"""
        try:
            doc_ref = self.db.collection('users').document(user_id)
            doc_ref.set({
                'last_match_at': timestamp,
                'updated_at': firestore.SERVER_TIMESTAMP
            }, merge=True)
            logger.info("User match timestamp updated", user_id=user_id)
            return True
        except Exception as e:
            logger.error("Failed to update match timestamp", user_id=user_id, error=str(e))
            return False
    
    # Scholarship Operations
    async def save_scholarship(self, scholarship: Scholarship) -> bool:
        """Save scholarship to Firestore.

        V2 FIX: Merge-write with field-level preservation so "fast"/thin scrapes
        never overwrite richer "deep" data (prize pools, deadlines, descriptions).
        """
        try:
            doc_ref = self.db.collection('scholarships').document(scholarship.id)

            incoming = scholarship.model_dump()
            existing_doc = doc_ref.get()

            if existing_doc.exists:
                existing = existing_doc.to_dict() or {}

                def _is_placeholder_amount_display(v: Any) -> bool:
                    s = str(v or '').strip().lower()
                    return s in {'', '$0', '0', 'see details', 'see listing', 'tbd', 'unknown', 'varies', 'prizes + swag (view details)'}

                # Preserve richer fields from existing if incoming is empty/placeholder.
                if float(incoming.get('amount') or 0) <= 0 and float(existing.get('amount') or 0) > 0:
                    incoming['amount'] = existing.get('amount')

                if _is_placeholder_amount_display(incoming.get('amount_display')) and not _is_placeholder_amount_display(existing.get('amount_display')):
                    incoming['amount_display'] = existing.get('amount_display')

                if not incoming.get('deadline') and existing.get('deadline'):
                    incoming['deadline'] = existing.get('deadline')
                    incoming['deadline_timestamp'] = existing.get('deadline_timestamp')

                if (not (incoming.get('description') or '').strip()) and (existing.get('description') or '').strip():
                    incoming['description'] = existing.get('description')

                # Union tags/geo/type tags for better UX.
                for key in ['tags', 'geo_tags', 'type_tags']:
                    inc = incoming.get(key) or []
                    ex = existing.get(key) or []
                    if isinstance(inc, list) and isinstance(ex, list):
                        incoming[key] = list(dict.fromkeys([*ex, *inc]))

            # Merge write to avoid wiping fields that the incoming model doesn't include.
            doc_ref.set(incoming, merge=True)
            logger.info("Scholarship saved", scholarship_id=scholarship.id, title=scholarship.title)
            return True
        except Exception as e:
            logger.error("Failed to save scholarship", scholarship_id=scholarship.id, error=str(e))
            raise
    
    async def get_scholarship(self, scholarship_id: str) -> Optional[Scholarship]:
        """Fetch single scholarship by ID"""
        try:
            doc_ref = self.db.collection('scholarships').document(scholarship_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                return Scholarship(**data)
            return None
        except Exception as e:
            logger.error("Failed to fetch scholarship", scholarship_id=scholarship_id, error=str(e))
            raise
    
    async def get_all_scholarships(self) -> List[Scholarship]:
        """Fetch all scholarships from cache"""
        try:
            docs = self.db.collection('scholarships').stream()
            scholarships = []
            
            for doc in docs:
                try:
                    scholarships.append(Scholarship(**doc.to_dict()))
                except Exception as parse_error:
                    logger.warning("Failed to parse scholarship", doc_id=doc.id, error=str(parse_error))
                    continue
            
            logger.info("Fetched scholarships", count=len(scholarships))
            return scholarships
        except Exception as e:
            logger.error("Failed to fetch all scholarships", error=str(e))
            raise
    
    async def get_user_matched_scholarships(self, user_id: str) -> List[Scholarship]:
        """Fetch scholarships matched to a specific user"""
        try:
            # Get user's matched scholarship IDs
            doc_ref = self.db.collection('user_matches').document(user_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                logger.info("No matched scholarships found", user_id=user_id)
                return []
            
            matched_ids = doc.to_dict().get('scholarship_ids', [])
            
            if not matched_ids:
                return []
            
            # Create references for batch fetch
            refs = [self.db.collection('scholarships').document(sid) for sid in matched_ids]
            
            # Fetch all documents in parallel (optimized batch read)
            docs = self.db.get_all(refs)
            
            scholarships = []
            now = datetime.now()
            
            for doc in docs:
                if doc.exists:
                    try:
                        data = doc.to_dict()
                        if 'id' not in data:
                            data['id'] = doc.id
                        
                        s = Scholarship(**data)
                        
                        # FILTER: Check if expired
                        if s.deadline:
                            try:
                                deadline_dt = datetime.fromisoformat(s.deadline.replace('Z', '+00:00'))
                                # Compare dates (ignoring time for simplicity/safety)
                                if deadline_dt.date() < now.date():
                                    continue # Skip expired
                            except Exception:
                                pass # Keep if date is weird
                                
                        scholarships.append(s)
                    except Exception as parse_error:
                        logger.warning("Failed to parse scholarship", doc_id=doc.id, error=str(parse_error))
                        continue
            
            logger.info("Fetched user matched scholarships", user_id=user_id, count=len(scholarships))
            return scholarships
        except Exception as e:
            logger.error("Failed to fetch user matched scholarships", user_id=user_id, error=str(e))
            raise
    
    async def save_user_matches(self, user_id: str, scholarship_ids: List[str]) -> bool:
        """Save matched scholarship IDs for a user"""
        try:
            doc_ref = self.db.collection('user_matches').document(user_id)
            doc_ref.set({
                'scholarship_ids': scholarship_ids,
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            logger.info("User matches saved", user_id=user_id, count=len(scholarship_ids))
            return True
        except Exception as e:
            logger.error("Failed to save user matches", user_id=user_id, error=str(e))
            raise

    async def add_user_match(self, user_id: str, scholarship_id: str) -> bool:
        """Add a SINGLE scholarship ID to user's matched list (Real-time update)"""
        try:
            doc_ref = self.db.collection('user_matches').document(user_id)
            doc_ref.set({
                'scholarship_ids': firestore.ArrayUnion([scholarship_id]),
                'updated_at': firestore.SERVER_TIMESTAMP
            }, merge=True)
            logger.info("Real-time match added to persistent pool", user_id=user_id, scholarship_id=scholarship_id)
            return True
        except Exception as e:
            logger.error("Failed to add individual user match", user_id=user_id, error=str(e))
            return False
    
    # Saved Scholarships Operations
    async def save_user_scholarship(self, user_id: str, scholarship_id: str) -> bool:
        """Add scholarship to user's saved list"""
        try:
            doc_ref = self.db.collection('users').document(user_id)
            # Use set with merge to create document if it doesn't exist
            doc_ref.set({
                'saved_scholarships': firestore.ArrayUnion([scholarship_id]),
                'updated_at': firestore.SERVER_TIMESTAMP
            }, merge=True)
            logger.info("Scholarship saved to user favorites", user_id=user_id, scholarship_id=scholarship_id)
            return True
        except Exception as e:
            logger.error("Failed to save scholarship to favorites", user_id=user_id, error=str(e))
            raise
    
    async def unsave_user_scholarship(self, user_id: str, scholarship_id: str) -> bool:
        """Remove scholarship from user's saved list"""
        try:
            doc_ref = self.db.collection('users').document(user_id)
            # Use set with merge to ensure document exists
            doc_ref.set({
                'saved_scholarships': firestore.ArrayRemove([scholarship_id]),
                'updated_at': firestore.SERVER_TIMESTAMP
            }, merge=True)
            logger.info("Scholarship removed from user favorites", user_id=user_id, scholarship_id=scholarship_id)
            return True
        except Exception as e:
            logger.error("Failed to remove scholarship from favorites", user_id=user_id, error=str(e))
            raise
    
    # Application Tracking & Management
    async def start_application(self, user_id: str, scholarship_id: str) -> str:
        """Track that user started an application, returns application_id"""
        try:
            # Check if draft already exists
            existing = self.db.collection('applications')\
                .where('user_id', '==', user_id)\
                .where('scholarship_id', '==', scholarship_id)\
                .where('status', '==', 'draft')\
                .limit(1)\
                .stream()
            
            for doc in existing:
                logger.info("Returning existing draft", application_id=doc.id)
                return doc.id
            
            # Create new draft
            doc_ref = self.db.collection('applications').document()
            application_id = doc_ref.id
            
            doc_ref.set({
                'application_id': application_id,
                'user_id': user_id,
                'scholarship_id': scholarship_id,
                'status': 'draft',
                'current_step': 1,
                'progress_percentage': 0.0,
                'personal_info': None,
                'documents': [],
                'essays': [],
                'recommenders': [],
                'additional_answers': {},
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'last_saved': firestore.SERVER_TIMESTAMP
            })
            
            logger.info("Application draft created", application_id=application_id, user_id=user_id, scholarship_id=scholarship_id)
            return application_id
        except Exception as e:
            logger.error("Failed to start application", user_id=user_id, error=str(e))
            raise
    
    async def save_application_draft(self, application_id: str, draft_data: Dict[str, Any]) -> bool:
        """Save application draft with auto-save data"""
        try:
            doc_ref = self.db.collection('applications').document(application_id)
            
            # Update only provided fields
            update_data = {
                'updated_at': firestore.SERVER_TIMESTAMP,
                'last_saved': firestore.SERVER_TIMESTAMP
            }
            
            if 'current_step' in draft_data:
                update_data['current_step'] = draft_data['current_step']
            if 'progress_percentage' in draft_data:
                update_data['progress_percentage'] = draft_data['progress_percentage']
            if 'personal_info' in draft_data and draft_data['personal_info'] is not None:
                update_data['personal_info'] = draft_data['personal_info']
            if 'documents' in draft_data and draft_data['documents'] is not None:
                update_data['documents'] = draft_data['documents']
            if 'essays' in draft_data and draft_data['essays'] is not None:
                update_data['essays'] = draft_data['essays']
            if 'recommenders' in draft_data and draft_data['recommenders'] is not None:
                update_data['recommenders'] = draft_data['recommenders']
            if 'additional_answers' in draft_data and draft_data['additional_answers'] is not None:
                update_data['additional_answers'] = draft_data['additional_answers']
            
            doc_ref.update(update_data)
            logger.info("Application draft saved", application_id=application_id)
            return True
        except Exception as e:
            logger.error("Failed to save draft", application_id=application_id, error=str(e))
            raise
    
    async def get_application_draft(self, user_id: str, scholarship_id: str) -> Optional[Dict[str, Any]]:
        """Get application draft for resume"""
        try:
            docs = self.db.collection('applications')\
                .where('user_id', '==', user_id)\
                .where('scholarship_id', '==', scholarship_id)\
                .where('status', '==', 'draft')\
                .limit(1)\
                .stream()
            
            for doc in docs:
                return doc.to_dict()
            
            return None
        except Exception as e:
            logger.error("Failed to get draft", user_id=user_id, scholarship_id=scholarship_id, error=str(e))
            raise
    
    async def submit_application(self, application_data: Dict[str, Any]) -> str:
        """Submit final application and generate confirmation number"""
        try:
            import secrets
            
            # Generate confirmation number
            confirmation_number = f"AS-{datetime.now().year}-{secrets.token_hex(6).upper()}"
            
            # Create submission document
            doc_ref = self.db.collection('applications').document(application_data['application_id'])
            
            submission_data = {
                **application_data,
                'status': 'submitted',
                'confirmation_number': confirmation_number,
                'submitted_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            
            doc_ref.set(submission_data)
            logger.info("Application submitted", application_id=application_data['application_id'], confirmation=confirmation_number)
            
            return confirmation_number
        except Exception as e:
            logger.error("Failed to submit application", error=str(e))
            raise
    
    async def get_user_applications(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all applications for a user"""
        try:
            docs = self.db.collection('applications')\
                .where('user_id', '==', user_id)\
                .order_by('updated_at', direction=firestore.Query.DESCENDING)\
                .stream()
            
            applications = []
            for doc in docs:
                applications.append(doc.to_dict())
            
            logger.info("Fetched user applications", user_id=user_id, count=len(applications))
            return applications
        except Exception as e:
            logger.error("Failed to fetch user applications", user_id=user_id, error=str(e))
            raise
    
    async def get_application_by_id(self, application_id: str) -> Optional[Dict[str, Any]]:
        """Get specific application by ID"""
        try:
            doc_ref = self.db.collection('applications').document(application_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            logger.error("Failed to fetch application", application_id=application_id, error=str(e))
            raise
    
    async def update_application_status(self, application_id: str, status: str, **kwargs) -> bool:
        """Update application status (for admin or automated updates)"""
        try:
            doc_ref = self.db.collection('applications').document(application_id)
            
            update_data = {
                'status': status,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            
            # Add optional fields
            if 'decision_date' in kwargs:
                update_data['decision_date'] = kwargs['decision_date']
            if 'award_amount' in kwargs:
                update_data['award_amount'] = kwargs['award_amount']
            if 'notes' in kwargs:
                update_data['notes'] = kwargs['notes']
            
            doc_ref.update(update_data)
            logger.info("Application status updated", application_id=application_id, status=status)
            return True
        except Exception as e:
            logger.error("Failed to update status", application_id=application_id, error=str(e))
            raise
    
    # Discovery Job Tracking
    async def create_discovery_job(self, user_id: str, job_id: str) -> bool:
        """Create a discovery job record"""
        try:
            doc_ref = self.db.collection('discovery_jobs').document(job_id)
            doc_ref.set({
                'user_id': user_id,
                'status': 'processing',
                'progress': 0,
                'scholarships_found': 0,
                'started_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            logger.info("Discovery job created", job_id=job_id, user_id=user_id)
            return True
        except Exception as e:
            logger.error("Failed to create discovery job", job_id=job_id, error=str(e))
            raise
    
    async def update_discovery_job(self, job_id: str, status: str, progress: float, scholarships_found: int) -> bool:
        """Update discovery job progress"""
        try:
            doc_ref = self.db.collection('discovery_jobs').document(job_id)
            doc_ref.update({
                'status': status,
                'progress': progress,
                'scholarships_found': scholarships_found,
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            return True
        except Exception as e:
            logger.error("Failed to update discovery job", job_id=job_id, error=str(e))
            raise
    
    async def get_discovery_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get discovery job status"""
        try:
            doc_ref = self.db.collection('discovery_jobs').document(job_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            logger.error("Failed to fetch discovery job", job_id=job_id, error=str(e))
            raise
    
    # Chat History Operations
    async def save_chat_message(self, user_id: str, role: str, content: str) -> bool:
        """Save a chat message to conversation history"""
        try:
            doc_ref = self.db.collection('chat_history').document(user_id).collection('messages').document()
            doc_ref.set({
                'role': role,
                'content': content,
                'timestamp': firestore.SERVER_TIMESTAMP
            })
            logger.info("Chat message saved", user_id=user_id, role=role)
            return True
        except Exception as e:
            logger.error("Failed to save chat message", user_id=user_id, error=str(e))
            # Don't raise - chat should continue even if history fails
            return False
    
    async def get_chat_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history for a user"""
        try:
            messages = self.db.collection('chat_history').document(user_id).collection('messages')\
                .order_by('timestamp', direction=firestore.Query.DESCENDING)\
                .limit(limit)\
                .stream()
            
            history = []
            for msg in messages:
                history.append(msg.to_dict())
            
            # Reverse to get chronological order
            history.reverse()
            
            logger.info("Fetched chat history", user_id=user_id, count=len(history))
            return history
        except Exception as e:
            logger.error("Failed to fetch chat history", user_id=user_id, error=str(e))
            return []
    
    async def clear_chat_history(self, user_id: str) -> bool:
        """Clear conversation history for a user"""
        try:
            messages = self.db.collection('chat_history').document(user_id).collection('messages').stream()
            
            batch = self.db.batch()
            count = 0
            for msg in messages:
                batch.delete(msg.reference)
                count += 1
                
                # Firestore batch limit is 500
                if count >= 500:
                    batch.commit()
                    batch = self.db.batch()
                    count = 0
            
            if count > 0:
                batch.commit()
            
            logger.info("Chat history cleared", user_id=user_id)
            return True
        except Exception as e:
            logger.error("Failed to clear chat history", user_id=user_id, error=str(e))
            raise

    # ============ SEMANTIC VECTOR SEARCH ============
    
    def _cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """
        Compute cosine similarity between two vectors.
        Returns value between -1 and 1 (higher = more similar).
        """
        if not vec_a or not vec_b:
            return 0.0
        
        if len(vec_a) != len(vec_b):
            logger.warning("Vector dimension mismatch", dim_a=len(vec_a), dim_b=len(vec_b))
            return 0.0
        
        import math
        
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        magnitude_a = math.sqrt(sum(a * a for a in vec_a))
        magnitude_b = math.sqrt(sum(b * b for b in vec_b))
        
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
        
        return dot_product / (magnitude_a * magnitude_b)
    
    async def semantic_search(
        self, 
        query_embedding: List[float], 
        limit: int = 20,
        min_similarity: float = 0.55
    ) -> List[Scholarship]:
        """
        Search scholarships by vector similarity.
        
        Uses in-memory cosine similarity over all opportunities with embeddings.
        This is the MVP approach - for production scale, consider:
        - Firestore Vector Search (when GA)
        - Pinecone / Weaviate for dedicated vector DB
        
        Args:
            query_embedding: 768-dim embedding of the search query
            limit: Maximum results to return
            min_similarity: Minimum cosine similarity threshold (0.0 to 1.0)
            
        Returns:
            List of Scholarship objects sorted by similarity score (highest first)
        """
        try:
            all_scholarships = await self.get_all_scholarships()
            scored = []
            
            embedding_count = 0
            
            for scholarship in all_scholarships:
                # Skip opportunities without embeddings
                if not scholarship.embedding:
                    continue
                
                embedding_count += 1
                
                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_embedding, scholarship.embedding)
                
                if similarity >= min_similarity:
                    # Attach similarity score for later use
                    scholarship.match_score = round(similarity * 100, 1)
                    scored.append((similarity, scholarship))
            
            # Sort by similarity descending
            scored.sort(key=lambda x: x[0], reverse=True)
            
            results = [s[1] for s in scored[:limit]]
            
            logger.info(
                "Semantic search completed",
                total_scanned=len(all_scholarships),
                with_embeddings=embedding_count,
                matches_found=len(results),
                min_similarity=min_similarity
            )
            
            return results
            
        except Exception as e:
            logger.error("Semantic search failed", error=str(e))
            return []


# Global database instance
db = FirebaseDB()


# Helper functions for easy imports
async def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Helper function to get user profile (for WebSocket and other imports)"""
    return await db.get_user_profile(user_id)
