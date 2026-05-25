import logging
import sys
import structlog
from structlog.types import Processor, EventDict
from collections.abc import Sequence
from contextvars import ContextVar
from typing import Any
from uuid import uuid4


def configure_logging(
    *,
    log_level: str = 'INFO',
    dev_mode: bool = False
) -> None:
    """
    Configure structured logging across the application.
    Call this as early as possible on app startup, preferably in a lifespan event
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Shared processors for both structlog and standard logging
    shared_processors: Sequence[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt='iso'),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        add_request_context
    ]

    # JSON or console rendering
    if dev_mode:
        renderer = structlog.dev.ConsoleRenderer(
            colors=True,
            exception_formatter=structlog.dev.plain_traceback
        )
        shared_processors.append(structlog.processors.format_exc_info)
    else:
        renderer: Processor = structlog.processors.JSONRenderer()
        shared_processors.append(structlog.processors.dict_tracebacks)

    # Structlog processor chain
    structlog_processors: Sequence[Processor] = [
        *shared_processors,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ]

    # Standard library processor chain
    stdlib_processors: Sequence[Processor] = [
        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
        renderer,
    ]

    # Configure structlog
    structlog.configure(
        processors=structlog_processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=stdlib_processors,
    )

    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(level)
    root_logger.addHandler(handler)

    # Encapsulate 3rd party loggers
    configure_third_party_loggers()


# Thread-safe context storage
request_context: ContextVar[dict[str, Any]] = ContextVar('request_context')


def get_correlation_id() -> str:
    """Get the current correlation ID or generate a new one"""
    try:
        ctx = request_context.get()
        return ctx.get('correlation_id', str(uuid4()))
    except LookupError:
        return str(uuid4())


def set_correlation_id(correlation_id: str | None = None) -> str:
    """Set or generate a correlation ID for the current request"""
    cid = correlation_id or str(uuid4())
    try:
        ctx = request_context.get().copy()
    except LookupError:
        ctx = {}

    ctx['correlation_id'] = cid
    request_context.set(ctx)
    return cid


def bind_request_context(**kwargs: Any) -> None:
    """Bind additional context to the current request"""
    try:
        ctx = request_context.get().copy()
    except LookupError:
        ctx = {}

    ctx.update(kwargs)
    request_context.set(ctx)


def clear_request_context() -> None:
    """Clear the request context"""
    request_context.set({})


def add_request_context(
        logger: logging.Logger,
        method_name: str,
        event_dict: EventDict
) -> EventDict:
    """Add request context to every log entry"""
    try:
        ctx = request_context.get()
        if ctx:
            event_dict.update(ctx)
    except LookupError:
        pass
    return event_dict


def configure_third_party_loggers(level: int = 20) -> None:
    """Reduce noise from third-party libraries"""
    # Suppress verbose HTTP libraries
    for logger_name in ('httpcore', 'httpx', 'hpack', 'urllib3'):
        logging.getLogger(logger_name).setLevel(
            max(level, logging.WARNING)
        )

    # Configure Uvicorn loggers
    uvicorn_loggers = (
        ('uvicorn', level),
        ('uvicorn.error', level),
        ('uvicorn.access', max(level, logging.WARNING)),
    )

    for logger_name, log_level in uvicorn_loggers:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = True  # Use root logger's handler
        logger.setLevel(log_level)
