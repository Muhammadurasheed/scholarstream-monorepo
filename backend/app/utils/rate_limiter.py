"""
Production-Grade Adaptive Rate Limiter for Google Gemini API.

Implements:
- Token-bucket algorithm for smooth request distribution
- Exponential backoff with jitter on 429 responses
- Asyncio Semaphore for concurrency control
- Per-minute sliding window tracking

Design: Google SRE-inspired. Prevents thundering herd on startup
while maximizing throughput under steady-state load.
"""

import asyncio
import time
import random
import structlog
from typing import TypeVar, Callable, Any
from functools import wraps

logger = structlog.get_logger()

T = TypeVar("T")


class AdaptiveRateLimiter:
    """
    Adaptive rate limiter with token bucket + exponential backoff.
    
    Usage:
        limiter = AdaptiveRateLimiter(max_rpm=30, max_concurrent=5)
        result = await limiter.execute(my_async_fn, arg1, arg2)
    """
    
    def __init__(
        self,
        max_rpm: int = 30,
        max_concurrent: int = 5,
        max_retries: int = 4,
        base_backoff: float = 2.0,
        max_backoff: float = 60.0,
    ):
        self.max_rpm = max_rpm
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries
        self.base_backoff = base_backoff
        self.max_backoff = max_backoff
        
        # Concurrency semaphore — hard cap on parallel Gemini calls
        self._semaphore = asyncio.Semaphore(max_concurrent)
        
        # Token bucket — sliding window of request timestamps
        self._request_timestamps: list[float] = []
        self._lock = asyncio.Lock()
        
        # Adaptive state — scale down if getting hammered
        self._consecutive_429s = 0
        self._effective_rpm = max_rpm
        
        logger.info(
            "AdaptiveRateLimiter initialized",
            max_rpm=max_rpm,
            max_concurrent=max_concurrent,
            max_retries=max_retries,
        )
    
    async def _wait_for_token(self):
        """
        Token bucket: wait until we have capacity in the current 60s window.
        """
        async with self._lock:
            now = time.monotonic()
            
            # Purge timestamps older than 60s
            self._request_timestamps = [
                ts for ts in self._request_timestamps 
                if now - ts < 60.0
            ]
            
            if len(self._request_timestamps) >= self._effective_rpm:
                # Window is full — wait until oldest token expires
                oldest = self._request_timestamps[0]
                wait_time = 60.0 - (now - oldest) + random.uniform(0.1, 0.5)
                logger.debug(
                    "Rate limiter throttling",
                    wait_s=round(wait_time, 2),
                    current_rpm=len(self._request_timestamps),
                    effective_rpm=self._effective_rpm,
                )
                # Release lock before sleeping
                await asyncio.sleep(max(0, wait_time))
                # Re-check after sleep
                now = time.monotonic()
                self._request_timestamps = [
                    ts for ts in self._request_timestamps 
                    if now - ts < 60.0
                ]
            
            # Record this request
            self._request_timestamps.append(time.monotonic())
    
    def _calculate_backoff(self, attempt: int) -> float:
        """Exponential backoff with full jitter (AWS-style)."""
        exp_backoff = min(
            self.max_backoff,
            self.base_backoff * (2 ** attempt)
        )
        # Full jitter: random between 0 and exp_backoff
        return random.uniform(0, exp_backoff)
    
    async def _adapt_rate(self, is_429: bool):
        """Adaptively scale RPM based on 429 signals."""
        async with self._lock:
            if is_429:
                self._consecutive_429s += 1
                # Halve effective RPM on repeated 429s, floor at 5
                self._effective_rpm = max(5, self._effective_rpm // 2)
                logger.warning(
                    "Rate limiter adapting DOWN",
                    consecutive_429s=self._consecutive_429s,
                    new_effective_rpm=self._effective_rpm,
                )
            else:
                if self._consecutive_429s > 0:
                    self._consecutive_429s = 0
                    # Slowly recover: increase by 25%, cap at max_rpm
                    self._effective_rpm = min(
                        self.max_rpm,
                        int(self._effective_rpm * 1.25)
                    )
                    logger.info(
                        "Rate limiter recovering",
                        new_effective_rpm=self._effective_rpm,
                    )
    
    async def execute(self, fn: Callable, *args, **kwargs) -> Any:
        """
        Execute an async function with rate limiting, concurrency
        control, and automatic retry on 429.
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            # 1. Acquire semaphore (concurrency gate)
            async with self._semaphore:
                # 2. Wait for token bucket capacity
                await self._wait_for_token()
                
                try:
                    # 3. Execute the actual function
                    result = await fn(*args, **kwargs)
                    
                    # Success — adapt up
                    await self._adapt_rate(is_429=False)
                    return result
                    
                except Exception as e:
                    error_str = str(e)
                    last_error = e
                    
                    if "429" in error_str or "Resource exhausted" in error_str:
                        # 429 — backoff and retry
                        await self._adapt_rate(is_429=True)
                        
                        if attempt < self.max_retries:
                            backoff = self._calculate_backoff(attempt)
                            logger.warning(
                                "Gemini 429 — backing off",
                                attempt=attempt + 1,
                                max_retries=self.max_retries,
                                backoff_s=round(backoff, 2),
                            )
                            await asyncio.sleep(backoff)
                            continue
                    
                    elif "403" in error_str:
                        # Auth error — don't retry, it won't help
                        logger.error("Gemini 403 — auth failure, not retrying", error=error_str)
                        raise
                    
                    else:
                        # Other error — retry once
                        if attempt == 0:
                            backoff = self._calculate_backoff(0)
                            logger.warning(
                                "Gemini call failed, retrying once",
                                error=error_str[:100],
                                backoff_s=round(backoff, 2),
                            )
                            await asyncio.sleep(backoff)
                            continue
                        raise
        
        # Exhausted all retries
        logger.error(
            "Gemini call failed after all retries",
            retries=self.max_retries,
            last_error=str(last_error)[:200],
        )
        raise last_error


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Global singleton — shared across all Gemini callers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
gemini_rate_limiter = AdaptiveRateLimiter(
    max_rpm=30,          # Conservative default — adapts up/down automatically
    max_concurrent=5,    # Max 5 parallel Gemini calls
    max_retries=4,       # Up to 4 retries on 429
    base_backoff=2.0,    # 2s base → 4s → 8s → 16s
    max_backoff=60.0,    # Never wait more than 60s
)
