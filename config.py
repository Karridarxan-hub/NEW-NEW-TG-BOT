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
    
    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()