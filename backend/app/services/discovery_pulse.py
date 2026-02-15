
import json
import time
from typing import Dict, List, Any, Optional
import structlog
from upstash_redis import Redis
from app.config import settings

logger = structlog.get_logger()

class DiscoveryPulseService:
    """
    Real-time mission tracking via Redis.
    Provides transparency into what the Sentinel and AI Refinery are doing.
    """
    
    PULSE_KEY = "cortex:discovery:pulse"
    MISSION_TTL = 3600 # 1 hour
    
    def __init__(self):
        self.redis = None
        self.circuit_open = False
        self.circuit_reset_time = 0
        self.failure_count = 0
        self.MAX_FAILURES = 3
        self.CIRCUIT_TIMEOUT = 300 # 5 minutes disable on failure
        
        if settings.upstash_redis_rest_url and settings.upstash_redis_rest_token:
            try:
                self.redis = Redis(
                    url=settings.upstash_redis_rest_url,
                    token=settings.upstash_redis_rest_token
                )
            except Exception as e:
                logger.warning("Pulse: Redis connection failed", error=str(e))
                
    def announce_mission(self, mission_id: str, target: str, status: str = "active"):
        """Announce a new or updated mission"""
        if not self.redis or self._circuit_open(): return
        
        try:
            pulse_data = {
                "mission_id": mission_id,
                "target": target,
                "status": status,
                "timestamp": time.time(),
                "label": f"Sentinel is patrolling {target}" if status == "active" else f"Mission {status}"
            }
            # Use HSET to keep multiple active missions if needed, for now we just use a single key for 'current'
            self.redis.hset(self.PULSE_KEY, mission_id, json.dumps(pulse_data))
            self.redis.expire(self.PULSE_KEY, self.MISSION_TTL)
            logger.info("Pulse: Mission Announced", mission=target)
        except Exception as e:
            logger.error("Pulse: Announcement failed", error=str(e))
            self._record_failure()

    def _circuit_open(self) -> bool:
        """Check if circuit is open (disabled)"""
        if self.circuit_open:
            if time.time() > self.circuit_reset_time:
                self.circuit_reset_time = 0
                self.circuit_open = False
                self.failure_count = 0
                logger.info("Pulse: Circuit Breaker RESET. Retrying Redis.")
                return False
            return True
        return False

    def _record_failure(self):
        """Record a failure and trip circuit if threshold reached"""
        self.failure_count += 1
        if self.failure_count >= self.MAX_FAILURES:
            self.circuit_open = True
            self.circuit_reset_time = time.time() + self.CIRCUIT_TIMEOUT
            logger.error("Pulse: Circuit Breaker TRIPPED. Redis disabled for 5 minutes to prevent spam.")

    def complete_mission(self, mission_id: str, found_count: int = 0):
        """Mark a mission as completed and report yield"""
        if not self.redis or self._circuit_open(): return
        
        try:
            raw = self.redis.hget(self.PULSE_KEY, mission_id)
            if raw:
                data = json.loads(raw)
                data["status"] = "completed"
                data["found_count"] = found_count
                data["completed_at"] = time.time()
                data["label"] = f"Mission Complete: {found_count} items found on {data.get('target')}"
                
                # Keep completed missions for 5 minutes for UI feedback
                self.redis.hset(self.PULSE_KEY, mission_id, json.dumps(data))
                logger.info("Pulse: Mission Completed", target=data.get('target'), found=found_count)
            else:
                self.redis.hdel(self.PULSE_KEY, mission_id)
        except Exception as e:
            logger.error("Pulse: Completion log failed", error=str(e))
            self._record_failure()

    def get_active_missions(self) -> List[Dict[str, Any]]:
        """Retrieve all active/recently completed missions"""
        if not self.redis or self._circuit_open(): return []
        
        try:
            all_missions = self.redis.hgetall(self.PULSE_KEY)
            if not all_missions: return []
            
            missions = []
            now = time.time()
            for mid, raw in all_missions.items():
                data = json.loads(raw)
                # Filter out old completed missions (> 2 minutes)
                if data.get("status") == "completed" and (now - data.get("completed_at", 0)) > 120:
                    self.redis.hdel(self.PULSE_KEY, mid)
                    continue
                missions.append(data)
            
            return sorted(missions, key=lambda x: x.get('timestamp', 0), reverse=True)
        except Exception as e:
            logger.error("Pulse: Retrieval failed", error=str(e))
            self._record_failure()
            return []

# Global instance
discovery_pulse = DiscoveryPulseService()
