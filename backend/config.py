from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        env_prefix="STOCK_AGENT_",
        extra="ignore",
    )

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    USE_REDIS: bool = False

    # Tushare
    TUSHARE_TOKEN: Optional[str] = None

    # Cache TTLs (seconds)
    REALTIME_CACHE_TTL: int = 10
    QUOTE_CACHE_TTL: int = 15
    SECTOR_CACHE_TTL: int = 30
    CAPITAL_FLOW_CACHE_TTL: int = 20
    FUNDAMENTALS_CACHE_TTL: int = 3600

    # HTTP settings
    HTTP_TIMEOUT: int = 8
    RETRY_ATTEMPTS: int = 3
    RETRY_DELAY: float = 1.0

    # Refresh
    DEFAULT_REFRESH_INTERVAL: int = 10

    # Rate limiting
    MAX_CONCURRENT_REQUESTS: int = 10
    REQUEST_QUEUE_SIZE: int = 100

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

@lru_cache()
def get_settings() -> Settings:
    return Settings()
