"""
In-Memory Event Broker (Adapter)
Uses asyncio.Queue and direct callbacks for high-speed, local event routing.
"""
import asyncio
import structlog
from typing import Dict, Any, List, Callable, Awaitable
from collections import defaultdict
from app.core.events import EventBroker

logger = structlog.get_logger()

class MemoryBroker:
    """
    In-Memory implementation of EventBroker.
    Uses asyncio for asynchronous event dispatch.
    """
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._running = False
        self._queue: asyncio.Queue = asyncio.Queue()
        self._worker_task = None

    async def start(self) -> None:
        """Start the background dispatcher"""
        self._running = True
        self._worker_task = asyncio.create_task(self._dispatcher())
        logger.info("MemoryBroker started")

    async def stop(self) -> None:
        """Stop the dispatcher"""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("MemoryBroker stopped")

    async def publish(self, topic: str, key: str, payload: Dict[str, Any]) -> bool:
        """
        Publish event to the in-memory queue.
        Returns True immediately if queued.
        """
        if not self._running:
            logger.warning("MemoryBroker is not running, dropping event", topic=topic)
            return False

        event = {
            "topic": topic,
            "key": key,
            "payload": payload
        }
        await self._queue.put(event)
        return True

    async def subscribe(self, topic: str, handler: Callable[[Dict[str, Any]], Awaitable[None]]) -> None:
        """Register a handler for a topic"""
        self._subscribers[topic].append(handler)
        logger.info("Handler subscribed", topic=topic, handler=handler.__name__)

    async def _dispatcher(self):
        """Background loop to process events from queue"""
        while self._running:
            try:
                event = await self._queue.get()
                topic = event["topic"]
                payload = event["payload"]
                
                handlers = self._subscribers.get(topic, [])
                if not handlers:
                    # Debug log only for unhandled topics to avoid noise
                    # logger.debug("No handlers for topic", topic=topic)
                    self._queue.task_done()
                    continue

                # Dispatch to all handlers concurrently
                tasks = [self._safe_execute(h, payload) for h in handlers]
                await asyncio.gather(*tasks)
                
                self._queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("MemoryBroker dispatcher error", error=str(e))

    async def _safe_execute(self, handler, payload):
        """Execute handler with error catching"""
        try:
            await handler(payload)
        except Exception as e:
            logger.error("EventHandler failed", handler=handler.__name__, error=str(e))
