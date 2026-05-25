import logging
from sqlalchemy import text, Connection
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine,
)
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from app.core.config import get_config

config = get_config()
logger = logging.getLogger(__name__)

engine: AsyncEngine = create_async_engine(
    config.db_url,
    # Connection pool configuration
    pool_size=config.db_pool_size,        # Permanent connections in pool
    max_overflow=config.db_max_overflow,  # Temporary connections during spikes
    pool_timeout=config.db_pool_timeout,  # Wait time for connection
    pool_recycle=config.db_pool_recycle,  # Prevent stale connections
    pool_pre_ping=True,                   # Verify connection before use
    echo=config.db_echo,                  # SQL logging for debugging
    connect_args={'server_settings': {'timezone': 'UTC'}}
)
logger.debug('<< database engine created >>')

# Create async session factory
# expire_on_commit=False prevents attribute access errors after commit
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Keep data accessible after commit
    autocommit=False,        # Require explicit commits
    autoflush=False,         # Manual control over flushing
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session for each request.

    The session is automatically closed when the request completes,
    even if an exception occurs. This prevents connection leaks.
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            # Rollback on any exception to maintain data integrity
            await session.rollback()
            raise
        finally:
            # Session is automatically closed by the context manager
            pass


@asynccontextmanager
async def get_db_session_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for use outside of FastAPI requests.

    Useful for background tasks, CLI commands, and tests.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def ping(conn: Connection):
    result = conn.execute(text("SELECT 1"))
    return result.fetchone()
