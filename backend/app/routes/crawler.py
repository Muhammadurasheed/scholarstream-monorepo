
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional
import asyncio
import json
import uuid
import structlog
from datetime import datetime
from app.services.kafka_config import KafkaConfig, kafka_producer_manager

router = APIRouter()
logger = structlog.get_logger()

# Sentinel Manager
class SentinelManager:
    """Manages connections to Sentinel Extension Crawlers"""
    
    def __init__(self):
        self.sentinels: Dict[str, WebSocket] = {}
        self.pending_jobs: Dict[str, asyncio.Future] = {}
        self.kafka_initialized = kafka_producer_manager.initialize()

    async def connect(self, node_id: str, websocket: WebSocket):
        await websocket.accept()
        self.sentinels[node_id] = websocket
        logger.info("Sentinel Node Connected", node_id=node_id)

    def disconnect(self, node_id: str):
        if node_id in self.sentinels:
            del self.sentinels[node_id]
            logger.info("Sentinel Node Disconnected", node_id=node_id)

    def get_available_node(self) -> Optional[str]:
        """Load balancing: Round Robin or Random"""
        if not self.sentinels:
            return None
        # Simple: return first available
        return list(self.sentinels.keys())[0]

    async def dispatch_crawl_job(self, url: str) -> bool:
        """
        Send a crawl job to a Sentinel Node.
        """
        node_id = self.get_available_node()
        if not node_id:
            logger.warning("No Sentinel Nodes available for crawl", url=url)
            return False

        job_id = str(uuid.uuid4())
        logger.info("Dispatching Crawl Job", job_id=job_id, node_id=node_id, url=url)
        
        try:
            ws = self.sentinels[node_id]
            await ws.send_json({
                "type": "crawl_request",
                "job_id": job_id,
                "url": url,
                "timestamp": datetime.utcnow().isoformat()
            })
            return True
        except Exception as e:
            logger.error("Failed to dispatch job", error=str(e))
            self.disconnect(node_id)
            return False

    async def handle_crawl_result(self, result: Dict):
        """Process HTML result from Sentinel"""
        job_id = result.get("job_id")
        url = result.get("url")
        html = result.get("html")
        status = result.get("status")
        
        if status == 200 and html:
            logger.info("Crawler Job Success", job_id=job_id, url=url, size=len(html))
            
            # Stream to Kafka
            if self.kafka_initialized:
                payload = {
                    "url": url,
                    "html": html,
                    "crawled_at": datetime.utcnow().timestamp(),
                    "source": self._extract_domain(url),
                    "method": "extension_sentinel"
                }
                kafka_producer_manager.publish_to_stream(
                    topic=KafkaConfig.RAW_HTML_TOPIC,
                    key=url,
                    value=payload
                )
                kafka_producer_manager.flush()
        else:
            logger.warning("Crawler Job Failed", job_id=job_id, status=status, url=url)

    def _extract_domain(self, url: str) -> str:
        from urllib.parse import urlparse
        return urlparse(url).netloc

sentinel_manager = SentinelManager()

@router.websocket("/ws/crawler")
async def websocket_endpoint(websocket: WebSocket):
    """Sentinel Extension connects here"""
    # Temporary ID until registration
    current_node_id = str(uuid.uuid4())
    is_registered = False
    
    try:
        # Initial connection
        await websocket.accept()
        logger.info("Sentinel WebSocket Connected", temp_id=current_node_id)
        
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            
            if msg.get("type") == "register":
                # Official Registration
                # If we were already registered with a temp ID, we might need to swap (but usually register comes first)
                provided_id = msg.get("node_id")
                
                if provided_id:
                    current_node_id = provided_id
                    sentinel_manager.sentinels[current_node_id] = websocket
                    is_registered = True
                    logger.info("Sentinel Registered", node_id=current_node_id)
                else:
                    # Just use temp
                    sentinel_manager.sentinels[current_node_id] = websocket
                    is_registered = True
                
            elif msg.get("type") == "crawl_result":
                # Result received
                await sentinel_manager.handle_crawl_result(msg)
                
            elif msg.get("type") == "crawl_error":
                logger.error("Sentinel Error", error=msg.get("error"), url=msg.get("url"))
                
            elif msg.get("type") == "heartbeat":
                # Responsd to keep alive
                pass

    except WebSocketDisconnect:
        logger.warning("Sentinel Disconnected", node_id=current_node_id)
        if is_registered:
            sentinel_manager.disconnect(current_node_id)
            
    except Exception as e:
        logger.error("Sentinel WS Error", error=str(e), node_id=current_node_id)
        if is_registered:
            sentinel_manager.disconnect(current_node_id)
