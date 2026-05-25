from fastapi import APIRouter, Request, Response, status
from sqlalchemy import event
from sqlalchemy.pool import Pool
import structlog
import time

from app.core.config import get_config
from app.data.database import engine, ping

logger = structlog.get_logger(__name__)
config = get_config()
health_router = APIRouter(prefix='/health')


@health_router.get('/')
async def health_check(request: Request):
    return {
        'status': 'healthy',
        'app_name': request.app.title,
        'version': request.app.version,
        'environment': config.environment
    }


@health_router.get('/db')
async def db_health_check(response: Response):
    try:
        async with engine.connect() as conn:
            start_time = time.perf_counter()
            await conn.run_sync(ping)
            ping_duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    except Exception:
        logger.exception("db_error")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {
            'status': 'unhealthy'
        }
    pool_stats = await get_pool_stats(engine)
    return {
        'status': 'healthy',
        'database': 'connected',
        'ping_duration_ms': ping_duration_ms,
        'connection_pool_info': pool_stats
    }


def setup_pool_monitoring(engine):
    """
    Set up connection pool event listeners for monitoring.

    Logs pool events and can emit metrics to monitoring systems.
    """

    @event.listens_for(Pool, 'connect')
    def on_connect(dbapi_conn, connection_record):
        '''Called when a new connection is created.'''
        logger.info('New database connection created')

    @event.listens_for(Pool, 'checkout')
    def on_checkout(dbapi_conn, connection_record, connection_proxy):
        '''Called when a connection is retrieved from the pool.'''
        logger.debug('Connection checked out from pool')

    @event.listens_for(Pool, 'checkin')
    def on_checkin(dbapi_conn, connection_record):
        '''Called when a connection is returned to the pool.'''
        logger.debug('Connection returned to pool')

    @event.listens_for(Pool, 'reset')
    def on_reset(dbapi_conn, connection_record):
        '''Called when a connection is reset before being returned.'''
        logger.debug('Connection reset')


async def get_pool_stats(engine) -> dict:
    """
    Get current connection pool statistics.

    Useful for monitoring dashboards and alerts.
    """
    pool = engine.pool
    return {
        'pool_size': pool.size(),
        'checked_in': pool.checkedin(),
        'checked_out': pool.checkedout(),
        'overflow': pool.overflow(),
        'invalid': pool.invalidatedcount if hasattr(pool, 'invalidatedcount') else 0,
    }
