"""
Event Broker Interface (Port)
Defines the contract for event publishing and subscription.
"""
from typing import Dict, Any, Protocol, Callable, Awaitable

class EventBroker(Protocol):
    """
    Abstract Protocol for an Event Broker.
    Allows switching between MemoryBroker and KafkaBroker.
    """
    
    async def start(self) -> None:
        """Initialize the broker"""
        ...

    async def stop(self) -> None:
        """Shutdown the broker"""
        ...

    async def publish(self, topic: str, key: str, payload: Dict[str, Any]) -> bool:
        """Publish an event to a topic"""
        ...

    async def subscribe(self, topic: str, handler: Callable[[Dict[str, Any]], Awaitable[None]]) -> None:
        """Subscribe a handler to a topic"""
        ...
