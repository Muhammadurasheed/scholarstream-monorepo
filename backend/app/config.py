"""
Configuration management for ScholarStream Backend
Handles environment variables and application settings
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    debug: bool = Field(default=True, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Firebase Configuration
    firebase_project_id: Optional[str] = Field(default=None, env="FIREBASE_PROJECT_ID")
    firebase_private_key_id: Optional[str] = Field(default=None, env="FIREBASE_PRIVATE_KEY_ID")
    firebase_private_key: Optional[str] = Field(default=None, env="FIREBASE_PRIVATE_KEY")
    firebase_client_email: Optional[str] = Field(default=None, env="FIREBASE_CLIENT_EMAIL")
    firebase_client_id: Optional[str] = Field(default=None, env="FIREBASE_CLIENT_ID")
    firebase_auth_uri: Optional[str] = Field(default="https://accounts.google.com/o/oauth2/auth", env="FIREBASE_AUTH_URI")
    firebase_token_uri: Optional[str] = Field(default="https://oauth2.googleapis.com/token", env="FIREBASE_TOKEN_URI")
    firebase_auth_provider_x509_cert_url: Optional[str] = Field(default="https://www.googleapis.com/oauth2/v1/certs", env="FIREBASE_AUTH_PROVIDER_X509_CERT_URL")
    firebase_client_x509_cert_url: Optional[str] = Field(default=None, env="FIREBASE_CLIENT_X509_CERT_URL")
    
    # Google Gemini AI
    gemini_api_key: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-1.5-flash", env="GEMINI_MODEL")
    
    # Upstash Redis Configuration (HTTP-based serverless Redis)
    upstash_redis_rest_url: str = Field(default="", env="UPSTASH_REDIS_REST_URL")
    upstash_redis_rest_token: str = Field(default="", env="UPSTASH_REDIS_REST_TOKEN")
    
    # CORS Settings (stored as comma-separated string)
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        env="CORS_ORIGINS"
    )
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    gemini_rate_limit_per_hour: int = Field(default=1000, env="GEMINI_RATE_LIMIT_PER_HOUR")
    
    # Caching
    scholarship_cache_ttl_hours: int = Field(default=24, env="SCHOLARSHIP_CACHE_TTL_HOURS")
    ai_enrichment_cache_ttl_hours: int = Field(default=168, env="AI_ENRICHMENT_CACHE_TTL_HOURS")
    
    
    # Cloudinary
    cloudinary_cloud_name: Optional[str] = Field(default=None, env="CLOUDINARY_CLOUD_NAME")
    cloudinary_api_key: Optional[str] = Field(default=None, env="CLOUDINARY_API_KEY")
    cloudinary_api_secret: Optional[str] = Field(default=None, env="CLOUDINARY_API_SECRET")
    
    # Confluent Kafka Configuration
    confluent_bootstrap_servers: str = Field(default="", env="CONFLUENT_BOOTSTRAP_SERVERS")
    confluent_api_key: str = Field(default="", env="CONFLUENT_API_KEY")
    confluent_api_secret: str = Field(default="", env="CONFLUENT_API_SECRET")
    kafka_raw_topic: str = Field(default="raw-opportunities-stream", env="KAFKA_RAW_TOPIC")
    kafka_enriched_topic: str = Field(default="enriched-opportunities-stream", env="KAFKA_ENRICHED_TOPIC")
    kafka_consumer_group_id: str = Field(default="scholarstream-websocket-consumer", env="KAFKA_CONSUMER_GROUP_ID")
    
    # Flink Configuration
    flink_app_name: str = Field(default="scholarstream-cortex", env="FLINK_APP_NAME")
    flink_parallelism: int = Field(default=1, env="FLINK_PARALLELISM")
    flink_checkpoint_interval: int = Field(default=60000, env="FLINK_CHECKPOINT_INTERVAL")
    
    # Cloud Function Configuration
    cloud_function_url: str = Field(default="", env="CLOUD_FUNCTION_URL")
    
    # WebSocket Configuration
    websocket_heartbeat_interval: int = Field(default=30, env="WEBSOCKET_HEARTBEAT_INTERVAL")
    websocket_reconnect_max_attempts: int = Field(default=10, env="WEBSOCKET_RECONNECT_MAX_ATTEMPTS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"
        
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse comma-separated CORS origins into a list"""
        return [origin.strip() for origin in self.cors_origins.split(',') if origin.strip()]
    
    @property
    def firebase_credentials(self) -> dict:
        """Format Firebase credentials for admin SDK initialization"""
        private_key = self.firebase_private_key
        if private_key:
            private_key = private_key.replace('\\n', '\n')
            
        return {
            "type": "service_account",
            "project_id": self.firebase_project_id,
            "private_key_id": self.firebase_private_key_id,
            "private_key": private_key,
            "client_email": self.firebase_client_email,
            "client_id": self.firebase_client_id,
            "auth_uri": self.firebase_auth_uri,
            "token_uri": self.firebase_token_uri,
            "auth_provider_x509_cert_url": self.firebase_auth_provider_x509_cert_url,
            "client_x509_cert_url": self.firebase_client_x509_cert_url,
        }


# Global settings instance
settings = Settings()
