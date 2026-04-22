"""
结构化日志工具 - 使用structlog
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

_LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def configure_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    level = _LOG_LEVELS.get(log_level.upper(), logging.INFO)

    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=True, exception_formatter=structlog.dev.plain_traceback
            )
        )

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """获取日志记录器"""
    return structlog.get_logger(name)


class LogContext:
    """日志上下文管理器"""

    def __init__(self, **kwargs: Any) -> None:
        self._context = kwargs

    def __enter__(self) -> "LogContext":
        for key, value in self._context.items():
            structlog.contextvars.bind_contextvars(**{key: value})
        return self

    def __exit__(self, *args: Any) -> None:
        for key in self._context:
            structlog.contextvars.unbind_contextvars(key)
