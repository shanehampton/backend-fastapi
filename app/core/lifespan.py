from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text
import structlog

from app.data.database import engine
from app.data.models.base import BaseModel
from app.core.monitoring import setup_pool_monitoring
from app.core.logging import configure_logging
from app.core.config import get_config, Environment

logger = structlog.get_logger(__name__)
config = get_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle events

    - Startup: Initialize database, configure logging, and set up monitoring events
    - Shutdown: Clean up database connections
    """
    # Startup
    if config.environment == Environment.development:
        dev_mode = True
    else:
        dev_mode = False

    configure_logging(
        log_level=config.log_level,
        dev_mode=dev_mode
    )
    logger.info('Application starting')
    setup_pool_monitoring(engine)

    # Create tables in development (use migrations in production)
    async with engine.begin() as conn:
        # Uncomment to auto-create tables during development
        await conn.run_sync(BaseModel.metadata.create_all)
        logger.info('Database tables initialized')

    async with engine.connect() as conn:
        await conn.execute(text('SELECT 1'))
        logger.info('Database ping successful')

    yield

    # Shutdown
    logger.info('Shutting down...')

    # Dispose of connection pool
    await engine.dispose()
    logger.info('Database connections closed')
