"""
HTTP客户端封装 - 支持重试、UA、代理
"""

from dataclasses import dataclass
from typing import Self

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from ..utils.logger import get_logger
from ..utils.retry import http_retry

logger = get_logger(__name__)


@dataclass
class FetcherConfig:
    """HTTP客户端配置"""

    timeout: float = 30.0
    max_retries: int = 3
    min_retry_wait: float = 1.0
    max_retry_wait: float = 60.0
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    follow_redirects: bool = True
    max_redirects: int = 10


class Fetcher:
    """
    HTTP请求封装类，支持自动重试和配置化

    Usage:
        async with Fetcher(config) as fetcher:
            response = await fetcher.get("https://example.com")
    """

    def __init__(self, config: FetcherConfig | None = None) -> None:
        self._config = config or FetcherConfig()
        self._client: httpx.Client | None = None

    def __enter__(self) -> Self:
        """同步上下文管理器"""
        self._client = httpx.Client(
            timeout=httpx.Timeout(self._config.timeout),
            headers={"User-Agent": self._config.user_agent},
            follow_redirects=self._config.follow_redirects,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )
        logger.info("fetcher_initialized", config=self._config)
        return self

    def __exit__(self, *args: object) -> None:
        """关闭HTTP客户端"""
        if self._client:
            self._client.close()
            self._client = None
            logger.info("fetcher_closed")

    def get(self, url: str, **kwargs: object) -> httpx.Response:
        """
        发送GET请求（同步）

        Args:
            url: 目标URL
            **kwargs: 传递给httpx.get的额外参数

        Returns:
            httpx.Response对象

        Raises:
            httpx.HTTPError: 请求失败时抛出
        """
        return self._request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: object) -> httpx.Response:
        """发送POST请求（同步）"""
        return self._request("POST", url, **kwargs)

    def _request(self, method: str, url: str, **kwargs: object) -> httpx.Response:
        """
        发送HTTP请求

        Args:
            method: HTTP方法
            url: 目标URL
            **kwargs: 额外参数

        Returns:
            httpx.Response对象
        """
        if self._client is None:
            raise RuntimeError("Fetcher not initialized. Use 'with' statement.")

        logger.debug("http_request", method=method, url=url)

        @http_retry(
            max_attempts=self._config.max_retries,
            min_wait=self._config.min_retry_wait,
            max_wait=self._config.max_retry_wait,
        )
        def _do_request() -> httpx.Response:
            response = self._client.request(method, url, **kwargs)
            response.raise_for_status()
            logger.debug("http_response", status=response.status_code, url=url)
            return response

        return _do_request()

    @property
    def client(self) -> httpx.Client:
        """获取HTTP客户端实例"""
        if self._client is None:
            raise RuntimeError("Fetcher not initialized.")
        return self._client


class AsyncFetcher:
    """
    异步HTTP请求封装类

    Usage:
        async with AsyncFetcher(config) as fetcher:
            response = await fetcher.get("https://example.com")
    """

    def __init__(self, config: FetcherConfig | None = None) -> None:
        self._config = config or FetcherConfig()
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> Self:
        """异步上下文管理器"""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self._config.timeout),
            headers={"User-Agent": self._config.user_agent},
            follow_redirects=self._config.follow_redirects,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )
        logger.info("async_fetcher_initialized", config=self._config)
        return self

    async def __aexit__(self, *args: object) -> None:
        """关闭HTTP客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("async_fetcher_closed")

    async def get(self, url: str, **kwargs: object) -> httpx.Response:
        """发送GET请求（异步）"""
        return await self._request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: object) -> httpx.Response:
        """发送POST请求（异步）"""
        return await self._request("POST", url, **kwargs)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True,
    )
    async def _request(self, method: str, url: str, **kwargs: object) -> httpx.Response:
        """
        发送异步HTTP请求

        Args:
            method: HTTP方法
            url: 目标URL
            **kwargs: 额外参数

        Returns:
            httpx.Response对象
        """
        if self._client is None:
            raise RuntimeError("AsyncFetcher not initialized. Use 'async with' statement.")

        logger.debug("async_http_request", method=method, url=url)

        response = await self._client.request(method, url, **kwargs)
        response.raise_for_status()
        logger.debug("async_http_response", status=response.status_code, url=url)
        return response

    @property
    def client(self) -> httpx.AsyncClient:
        """获取异步HTTP客户端实例"""
        if self._client is None:
            raise RuntimeError("AsyncFetcher not initialized.")
        return self._client
