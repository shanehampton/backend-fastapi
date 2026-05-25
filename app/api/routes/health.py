from fastapi import APIRouter, Request, Response, status
import structlog
from sqlalchemy import text
import time

from ..data.database import engine
from ..core.config import get_config

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
            await conn.execute(text('SELECT 1'))
            ping_duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            'status': 'healthy',
            'database': 'connected',
            'ping_duration_ms': ping_duration_ms
        }
    except Exception:
        logger.exception("db_error")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {
            'status': 'unhealthy'
        }
