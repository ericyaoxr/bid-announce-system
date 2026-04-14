"""
重试机制 - 基于tenacity
"""
from collections.abc import Callable
from typing import TypeVar

import httpx
from tenacity import (
    after_log,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .logger import get_logger

T = TypeVar("T")
logger = get_logger(__name__)


def http_retry(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 60.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    HTTP请求重试装饰器

    Args:
        max_attempts: 最大重试次数
        min_wait: 最小等待时间（秒）
        max_wait: 最大等待时间（秒）
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        before_sleep=before_sleep_log(logger, "warning"),
        after=after_log(logger, "debug"),
        reraise=True,
    )


def async_http_retry(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 60.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    异步HTTP请求重试装饰器
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException, httpx.ConnectError)),
        before_sleep=before_sleep_log(logger, "warning"),
        after=after_log(logger, "debug"),
        reraise=True,
    )
