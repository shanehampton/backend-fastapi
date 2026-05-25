from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import structlog

logger = structlog.get_logger(__name__)


class Environment(str, Enum):
    development = 'development'
    staging = 'staging'
    production = 'production'


class Config(BaseSettings):
    db_url: str
    db_pool_size: int = 5        # Number of connections to keep open
    db_max_overflow: int = 10    # Extra connections allowed during peak load
    db_pool_timeout: int = 30    # Seconds to wait for available connection
    db_pool_recycle: int = 1800  # Recycle connections after 30 minutes
    db_echo: bool = False

    environment: str = Environment.development
    log_level: str = 'INFO'

    default_page_size: int = 25

    model_config = SettingsConfigDict(
        env_file='.env',
        case_sensitive=False
    )


@lru_cache()
def get_config() -> Config:
    """Cache settings to avoid reading env file on every request."""
    logger.info('Reading app config')
    return Config()
