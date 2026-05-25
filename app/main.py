from fastapi import FastAPI, APIRouter, Request
from fastapi.responses import JSONResponse
import structlog

from app.core.config import get_config
from app.core.lifespan import lifespan
from app.middleware.request_logger import LoggingMiddleware
from app.api import routes

app = FastAPI(
    title='Backend-FastAPI',
    version='0.1.0',
    lifespan=lifespan
)
logger = structlog.get_logger(__name__)
config = get_config()

for key, value in config.model_dump().items():
    logger.info(f'config.{key} = {value}')

app.add_middleware(
    LoggingMiddleware
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Add consistent JSON response for unhandled exceptions"""
    return JSONResponse(
        status_code=500,
        content={'detail': 'An internal server error occurred.'},
    )

routers = [
    getattr(routes, name)
    for name in dir(routes)
    if isinstance(getattr(routes, name), APIRouter)
]
for router in routers:
    app.include_router(router)
