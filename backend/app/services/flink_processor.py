import structlog
import time
import hashlib
from typing import Dict, List, Any, Optional
from collections import deque
import asyncio

from app.config import settings

logger = structlog.get_logger()


def normalize_text(text: str) -> str:
    """Normalize text for consistent hashing"""
    if not text:
        return ""
    return " ".join(text.lower().strip().split())


def generate_content_fingerprint(data: Dict[str, Any]) -> str:
    """
    Generate a fingerprint based on core content for near-duplicate detection.
    Catches opportunities that are essentially the same but from different URLs.
    """
    title = normalize_text(data.get('name', data.get('title', '')))
    org = normalize_text(data.get('organization', data.get('org', '')))
    amount = str(data.get('amount', 0))
    deadline = data.get('deadline', '')
    
    content = f"{title}|{org}|{amount}|{deadline}"
    return hashlib.md5(content.encode()).hexdigest()


def generate_opportunity_id(opportunity: Dict[str, Any]) -> str:
    """
    Generate a STABLE, DETERMINISTIC ID for deduplication.
    Uses URL + normalized title + org for maximum stability.
    """
    url = opportunity.get('url') or opportunity.get('source_url') or ''
    title = normalize_text(opportunity.get('name') or opportunity.get('title') or '')
    org = normalize_text(opportunity.get('organization') or '')
    
    # Create composite key
    composite = f"{url}|{title}|{org}"
    
    # Generate stable hash with prefix
    hash_digest = hashlib.sha256(composite.encode()).hexdigest()[:16]
    return f"opp_{hash_digest}"


class CortexFlinkProcessor:
    """
    The Cortex Stream Processor (Python Native V3)
    
    ENHANCED DEDUPLICATION WITH FIRESTORE PERSISTENCE:
    1. Content-based hashing (URL + Title + Organization)
    2. Sliding window expiration (1 hour for memory, permanent in Firestore)
    3. Firestore-backed state for cross-restart deduplication
    """
    
    def __init__(self):
        self.window_size_seconds = 3600  # 1 Hour
        self.seen_opportunities = {}  # Map[content_hash, timestamp]
        self.processing_queue = deque()
        self.total_processed = 0
        self.duplicates_dropped = 0
        self._firestore_loaded = False
        logger.info("Cortex Processor Online (Engine: Native Python V3 - Firestore Persistence)")
        
    def _load_persisted_state(self):
        """
        Load existing scholarship IDs from Firestore for cross-restart deduplication.
        Called lazily on first process_event to avoid startup overhead.
        """
        if self._firestore_loaded:
            return
            
        try:
            import firebase_admin
            from firebase_admin import firestore as fs
            
            # Get Firestore client
            try:
                app = firebase_admin.get_app()
            except ValueError:
                logger.warning("Firebase not initialized, skipping state load")
                self._firestore_loaded = True
                return
                
            db = fs.client()
            
            # Load existing scholarship IDs (just the IDs, not full docs)
            docs = db.collection('scholarships').stream()
            now = time.time()
            
            count = 0
            for doc in docs:
                # Use document ID as the seen key
                self.seen_opportunities[doc.id] = now
                count += 1
                
            self._firestore_loaded = True
            logger.info("🔄 Loaded persisted state from Firestore", 
                       existing_count=count, 
                       cache_size=len(self.seen_opportunities))
                       
        except Exception as e:
            logger.error("Failed to load persisted state", error=str(e))
            self._firestore_loaded = True  # Mark as loaded to prevent retry loops
        
    async def process_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Ingest and process a single raw opportunity event.
        Returns None if duplicate, otherwise returns the enriched event.
        """
        # Lazy-load persisted state from Firestore (runs once)
        self._load_persisted_state()
        
        # Generate stable content-based ID
        content_id = generate_opportunity_id(event)
        url = event.get('url') or event.get('source_url') or ''
        
        now = time.time()
        
        # 1. DEDUPLICATION LOGIC (Permanent Content-based)
        # V4 FIX: Allow "better" updates to pass through (deep scrapes / enriched fields)
        # so low-quality first writes don't permanently block later improvements.
        if content_id in self.seen_opportunities:
            is_deep_source = any(
                s in str(event.get('source', '')).lower()
                for s in ['deep', 'dorahacks_deep', 'refinery', 'enriched']
            )
            has_new_signal = bool(event.get('amount') or event.get('deadline') or event.get('amount_display'))

            if not (is_deep_source or has_new_signal):
                self.duplicates_dropped += 1
                logger.debug(
                    "Duplicate Dropped (Cortex Shield)",
                    content_id=content_id[:8],
                    url=url[:50] if url else 'N/A',
                    total_dropped=self.duplicates_dropped,
                )
                return None  # Drop duplicate

            # Let it pass as an update event.
            event['is_update'] = True
            event['id'] = content_id
            event['cortex_processed_at'] = now
            logger.info(
                "Duplicate Allowed (Update)",
                content_id=content_id[:8],
                url=url[:50] if url else 'N/A',
                source=event.get('source'),
            )
            return event
            
        # Update state with stable ID
        self.seen_opportunities[content_id] = now
        
        # 2. ENRICH EVENT WITH STABLE ID & STANDARDIZE SCHEMA
        event['id'] = content_id  # Assign stable ID
        event['cortex_processed_at'] = now
        
        # Standardize 'name' (New Schema Compliance)
        if 'name' not in event and 'title' in event:
            event['name'] = event['title']

        # Standardize 'source_url' with multiple fallbacks
        if not event.get('source_url'):
            event['source_url'] = (
                event.get('url') or 
                event.get('apply_url') or 
                event.get('link') or 
                event.get('application_url') or
                ''
            )
        
        # CRITICAL: Construct URL from platform + slug if still missing
        if not event.get('source_url'):
            platform = str(event.get('source', '')).lower()
            slug = event.get('slug') or event.get('handle') or ''
            name = event.get('name') or event.get('title') or ''
            url_slug = slug or name.lower().replace(' ', '-').replace("'", "")[:50]
            
            if url_slug:
                if 'devpost' in platform:
                    event['source_url'] = f"https://{url_slug}.devpost.com/"
                elif 'dorahacks' in platform:
                    event['source_url'] = f"https://dorahacks.io/hackathon/{url_slug}"
                elif 'superteam' in platform or 'earn' in platform:
                    event['source_url'] = f"https://earn.superteam.fun/listings/{url_slug}"
                elif 'hackquest' in platform:
                    event['source_url'] = f"https://hackquest.io/events/{url_slug}"
                    
            if event.get('source_url'):
                logger.info("Constructed source_url from platform/slug", 
                           url=event['source_url'][:60], platform=platform)
        
        # 3. WINDOW MANAGEMENT
        self._cleanup_window(now)
        self.processing_queue.append((now, event))
        self.total_processed += 1
        
        logger.info(
            "Cortex Processed Event", 
            content_id=content_id[:8],
            url=url[:50] if url else 'N/A',
            window_count=len(self.processing_queue),
            total_processed=self.total_processed,
            duplicates_dropped=self.duplicates_dropped
        )
        
        return event

    def _cleanup_window(self, current_time: float):
        """Slide the window (Evict old events and stale seen entries)"""
        # Clean processing queue (only for windowed stats)
        while self.processing_queue:
            timestamp, _ = self.processing_queue[0]
            if (current_time - timestamp) > self.window_size_seconds:
                self.processing_queue.popleft()
            else:
                break
        
        # NOTE: We DO NOT evict from self.seen_opportunities anymore.
        # This fixes the bug where persistent history was lost every 2 hours,
        # causing 6-hour scrape intervals to re-add everything as duplicates.
        # 100k IDs = ~5MB RAM, which is acceptable for lifetime dedup.
        
        # stale_ids = [
        #     cid for cid, ts in self.seen_opportunities.items()
        #     if (current_time - ts) > self.window_size_seconds * 2
        # ]
        # if stale_ids:
        #    logger.debug("Evicted stale entries", count=len(stale_ids))

    def get_stats(self) -> Dict[str, Any]:
        """Get processor statistics"""
        return {
            'total_processed': self.total_processed,
            'duplicates_dropped': self.duplicates_dropped,
            'unique_in_window': len(self.processing_queue),
            'seen_cache_size': len(self.seen_opportunities),
            'deduplication_rate': f"{(self.duplicates_dropped / max(1, self.total_processed + self.duplicates_dropped)) * 100:.1f}%"
        }

    def is_duplicate(self, opportunity: Dict[str, Any]) -> bool:
        """Quick check if opportunity is a duplicate without processing"""
        content_id = generate_opportunity_id(opportunity)
        now = time.time()
        last_seen = self.seen_opportunities.get(content_id, 0)
        return (now - last_seen) < self.window_size_seconds


# Singleton for the app to use
cortex_processor = CortexFlinkProcessor()

if __name__ == "__main__":
    # Test Loop
    processor = CortexFlinkProcessor()
    
    async def test():
        # Test 1: First event should pass
        result1 = await processor.process_event({"url": "http://test.com", "name": "Test Scholarship"})
        print(f"Event 1: {'Processed' if result1 else 'Dropped'}")
        
        # Test 2: Same event should be dropped
        result2 = await processor.process_event({"url": "http://test.com", "name": "Test Scholarship"})
        print(f"Event 2: {'Processed' if result2 else 'Dropped'}")
        
        # Test 3: Different event should pass
        result3 = await processor.process_event({"url": "http://different.com", "name": "Different Scholarship"})
        print(f"Event 3: {'Processed' if result3 else 'Dropped'}")
        
        print(f"\nStats: {processor.get_stats()}")
    
    asyncio.run(test())
