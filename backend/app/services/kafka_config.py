"""
Confluent Kafka Configuration & Producer Management
Handles event streaming to Confluent Cloud topics
"""
import os
import json
from typing import Optional, Dict, Any
from confluent_kafka import Producer, KafkaError, KafkaException
from confluent_kafka.admin import AdminClient, NewTopic
import structlog


from app.config import settings

logger = structlog.get_logger()

class KafkaConfig:
    """Confluent Kafka configuration manager"""

    # --- THE CONFLUENT LIFELINE (System Manifest V1) ---
    # 1. Identity (Compacted)
    TOPIC_USER_IDENTITY = "user.identity.v1" 
    
    # 2. Cortex Command & Control
    TOPIC_CORTEX_COMMANDS = "cortex.commands.v1"
    
    # 3. Data Ingestion (High Throughput)
    TOPIC_RAW_HTML = "cortex.raw.html.v1"
    
    # 4. Intelligence & Delivery
    TOPIC_OPPORTUNITY_ENRICHED = "opportunity.enriched.v1"
    
    # 5. System Health
    TOPIC_SYSTEM_ALERTS = "system.alerts.v1"
    
    # 6. User Notifications
    TOPIC_USER_MATCHES = "user.matches.v1"

    def __init__(self):
        """Initialize Kafka configuration from settings"""
        self.bootstrap_servers = settings.confluent_bootstrap_servers
        self.api_key = settings.confluent_api_key
        self.api_secret = settings.confluent_api_secret
        self.enabled = all([self.bootstrap_servers, self.api_key, self.api_secret])

        if not self.enabled:
            logger.warning(
                "Kafka streaming disabled - missing Confluent credentials",
                bootstrap_servers=bool(self.bootstrap_servers),
                api_key=bool(self.api_key),
                api_secret=bool(self.api_secret)
            )
        else:
            logger.info(
                "Kafka Lifeline Enabled",
                bootstrap_servers=self.bootstrap_servers,
                topics=[
                    self.TOPIC_USER_IDENTITY,
                    self.TOPIC_CORTEX_COMMANDS,
                    self.TOPIC_RAW_HTML,
                    self.TOPIC_OPPORTUNITY_ENRICHED,
                    self.TOPIC_SYSTEM_ALERTS,
                    self.TOPIC_USER_MATCHES
                ]
            )

    def ensure_topics_exist(self):
        """Create V1 topics if they don't exist"""
        if not self.enabled:
            return

        admin_client = AdminClient({
            'bootstrap.servers': self.bootstrap_servers,
            'security.protocol': 'SASL_SSL',
            'sasl.mechanism': 'PLAIN',
            'sasl.username': self.api_key,
            'sasl.password': self.api_secret
        })

        topics = [
            NewTopic(self.TOPIC_USER_IDENTITY, num_partitions=1, replication_factor=3),
            NewTopic(self.TOPIC_CORTEX_COMMANDS, num_partitions=1, replication_factor=3),
            NewTopic(self.TOPIC_RAW_HTML, num_partitions=1, replication_factor=3),
            NewTopic(self.TOPIC_OPPORTUNITY_ENRICHED, num_partitions=1, replication_factor=3),
            NewTopic(self.TOPIC_SYSTEM_ALERTS, num_partitions=1, replication_factor=3)
        ]

        # Call create_topics to asynchronously create topics.
        fs = admin_client.create_topics(topics)

        # Wait for each operation to finish.
        for topic, f in fs.items():
            try:
                f.result()  # The result itself is None
                logger.info(f"Topic {topic} created")
            except Exception as e:
                # Continue if topic already exists
                if "Topic" in str(e) and "exists" in str(e):
                    continue
                logger.warning(f"Failed to create topic {topic}: {e}")

    def get_producer_config(self) -> Dict[str, Any]:
        """Get Confluent Kafka producer configuration"""
        if not self.enabled:
            return {}

        return {
            'bootstrap.servers': self.bootstrap_servers,
            'security.protocol': 'SASL_SSL',
            'sasl.mechanism': 'PLAIN',
            'sasl.username': self.api_key,
            'sasl.password': self.api_secret,
            'acks': 'all',
            'retries': 5,  # Increased retries
            'max.in.flight.requests.per.connection': 5,
            'compression.type': 'snappy',
            'linger.ms': 100,
            'client.id': 'scholarstream-producer',
            # INFRASTRUCTURE HARDENING
            'socket.timeout.ms': 60000, 
            'reconnect.backoff.ms': 2000,
            'reconnect.backoff.max.ms': 15000,
            'request.timeout.ms': 30000,
        }

    def get_consumer_config(self, group_id: str = 'scholarstream-consumers') -> Dict[str, Any]:
        """Get Confluent Kafka consumer configuration"""
        if not self.enabled:
            return {}

        return {
            'bootstrap.servers': self.bootstrap_servers,
            'security.protocol': 'SASL_SSL',
            'sasl.mechanism': 'PLAIN',
            'sasl.username': self.api_key,
            'sasl.password': self.api_secret,
            'group.id': group_id,
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False,
            # CONSUMER RESILIENCE (Deep Sea Tuning for High Latency)
            'session.timeout.ms': 45000,
            'heartbeat.interval.ms': 3000,
            'socket.timeout.ms': 60000,
            'reconnect.backoff.ms': 2000,
            'reconnect.backoff.max.ms': 15000,
            'fetch.min.bytes': 1024 * 1024, # 1MB batching to handle 400ms RTT
            'fetch.wait.max.ms': 1000,     # Allow more time for batching
        }


class KafkaProducerManager:
    """
    Manages Kafka producer lifecycle and message publishing
    Thread-safe, reusable producer instance
    """

    def __init__(self):
        self.config = KafkaConfig()
        self._producer: Optional[Producer] = None
        self._is_initialized = False

    def initialize(self) -> bool:
        """
        Initialize Kafka producer
        Returns True if successful, False if Kafka is disabled
        """
        if not self.config.enabled:
            logger.info("Kafka producer not initialized - streaming disabled")
            return False

        if self._is_initialized:
            return True

        try:
            producer_config = self.config.get_producer_config()
            self._producer = Producer(producer_config)
            self._is_initialized = True
            logger.info("Kafka producer initialized successfully")
            return True

        except KafkaException as e:
            logger.error("Failed to initialize Kafka producer", error=str(e))
            return False

    def publish_to_stream(
        self,
        topic: str,
        key: str,
        value: Dict[str, Any],
        callback: Optional[callable] = None
    ) -> bool:
        """
        Publish message to Kafka topic

        Args:
            topic: Kafka topic name
            key: Message key (typically source name)
            value: Message payload as dictionary
            callback: Optional delivery callback

        Returns:
            True if message queued successfully, False otherwise
        """
        if not self._is_initialized:
            if not self.initialize():
                logger.debug("Skipping Kafka publish - producer not available")
                return False

        try:
            message_value = json.dumps(value).encode('utf-8')
            message_key = key.encode('utf-8')

            self._producer.produce(
                topic=topic,
                key=message_key,
                value=message_value,
                callback=callback or self._default_delivery_callback
            )

            self._producer.poll(0)

            logger.info(
                "Message published to Kafka",
                topic=topic,
                key=key,
                payload_size=len(message_value)
            )
            return True

        except BufferError:
            logger.warning(
                "Kafka buffer full - flushing and retrying",
                topic=topic,
                key=key
            )
            self._producer.flush()

            try:
                self._producer.produce(
                    topic=topic,
                    key=message_key,
                    value=message_value,
                    callback=callback or self._default_delivery_callback
                )
                self._producer.poll(0)
                return True
            except Exception as retry_error:
                logger.error("Failed to publish after buffer flush", error=str(retry_error))
                return False

        except KafkaException as e:
            logger.error(
                "Kafka publish error",
                topic=topic,
                key=key,
                error=str(e)
            )
            return False

    def _default_delivery_callback(self, err, msg):
        """Default callback for message delivery confirmation"""
        if err is not None:
            logger.error(
                "Message delivery failed",
                topic=msg.topic(),
                partition=msg.partition(),
                error=str(err)
            )
        else:
            logger.debug(
                "Message delivered successfully",
                topic=msg.topic(),
                partition=msg.partition(),
                offset=msg.offset()
            )

    def flush(self, timeout: float = 10.0):
        """
        Flush pending messages
        Blocks until all messages are delivered or timeout
        """
        if self._producer and self._is_initialized:
            pending = self._producer.flush(timeout)
            if pending > 0:
                logger.warning(f"{pending} messages still pending after flush")
            else:
                logger.debug("All messages flushed successfully")

    def close(self):
        """Close producer and flush remaining messages"""
        if self._producer and self._is_initialized:
            logger.info("Closing Kafka producer")
            self.flush()
            self._is_initialized = False


kafka_producer_manager = KafkaProducerManager()
