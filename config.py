from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    bot_token: str
    faceit_api_key: str
    webhook_url: Optional[str] = None
    debug: bool = False
    
    # Database settings
    database_url: Optional[str] = None
    redis_url: Optional[str] = None
    
    # Worker configuration
    stats_workers: int = 3
    history_workers: int = 2
    comparison_workers: int = 2
    notification_workers: int = 1
    
    # Performance settings
    concurrent_requests: int = 5
    batch_size: int = 10
    max_queue_size: int = 1000
    worker_timeout: int = 30
    
    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()