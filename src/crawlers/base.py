"""
采集数据基类 - 通用采集数据框架
"""
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Generic, TypeVar

from ..core.fetcher import AsyncFetcher
from ..core.parser import ListPageParser
from ..core.rate_limiter import RateLimiterBackend
from ..core.storage import BaseRepository
from ..models.announcement import Announcement
from ..utils.logger import LogContext, get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound=Announcement)


@dataclass
class CrawlResult(Generic[T]):
    """爬取结果封装"""
    success: bool
    items_fetched: int = 0
    items_new: int = 0
    items_updated: int = 0
    errors: list[str] = field(default_factory=list)
    duration_ms: int = 0
    data: list[T] | None = None

    @classmethod
    def ok(
        cls,
        items_fetched: int = 0,
        items_new: int = 0,
        items_updated: int = 0,
        duration_ms: int = 0,
        data: list[T] | None = None,
    ) -> "CrawlResult[T]":
        return cls(
            success=True,
            items_fetched=items_fetched,
            items_new=items_new,
            items_updated=items_updated,
            duration_ms=duration_ms,
            data=data,
        )

    @classmethod
    def fail(cls, errors: list[str], duration_ms: int = 0) -> "CrawlResult[T]":
        return cls(success=False, errors=errors, duration_ms=duration_ms)


@dataclass
class CrawlConfig:
    """采集数据配置"""
    target_url: str
    max_retries: int = 3
    timeout: float = 30.0
    rate_limit_rpm: int = 60  # 每分钟请求数
    batch_size: int = 50
    max_depth: int = 2


class BaseCrawler(ABC, Generic[T]):
    """
    采集数据基类

    Type Parameters:
        T: 数据模型类型

    Usage:
        class MyCrawler(BaseCrawler[Announcement]):
            async def crawl_list(self, page: int) -> CrawlResult[Announcement]:
                ...
    """

    def __init__(
        self,
        fetcher: AsyncFetcher,
        parser: ListPageParser,
        repository: BaseRepository[T],
        rate_limiter: RateLimiterBackend,
        config: CrawlConfig,
    ) -> None:
        self._fetcher = fetcher
        self._parser = parser
        self._repository = repository
        self._rate_limiter = rate_limiter
        self._config = config
        self._is_running = False
        self._stats = {
            "total_fetched": 0,
            "total_new": 0,
            "total_updated": 0,
            "total_errors": 0,
        }

    @property
    def is_running(self) -> bool:
        """采集数据是否正在运行"""
        return self._is_running

    @property
    def stats(self) -> dict[str, int]:
        """采集数据统计信息"""
        return self._stats.copy()

    async def crawl_with_rate_limit(self, url: str) -> str:
        """带限流的抓取"""
        await self._rate_limiter.acquire()
        response = await self._fetcher.get(url)
        return response.text

    @abstractmethod
    async def crawl_list(self, page: int, **kwargs) -> CrawlResult[T]:
        """
        抓取列表页

        Args:
            page: 页码
            **kwargs: 额外参数

        Returns:
            CrawlResult: 爬取结果
        """
        pass

    @abstractmethod
    async def crawl_detail(self, item_id: str, **kwargs) -> CrawlResult[T]:
        """
        抓取详情页

        Args:
            item_id: 条目ID
            **kwargs: 额外参数

        Returns:
            CrawlResult: 爬取结果
        """
        pass

    async def crawl_paginated(
        self,
        start_page: int = 1,
        end_page: int | None = None,
        max_pages: int = 100,
    ) -> AsyncIterator[CrawlResult[T]]:
        """
        分页爬取

        Args:
            start_page: 起始页
            end_page: 结束页（None表示直到没有数据）
            max_pages: 最大页数限制

        Yields:
            CrawlResult: 每页的爬取结果
        """
        page = start_page
        consecutive_empty = 0

        while page <= max_pages:
            if end_page and page > end_page:
                break

            with LogContext(crawler=self.__class__.__name__, page=page):
                result = await self.crawl_list(page)

                if not result.success:
                    consecutive_empty += 1
                    if consecutive_empty >= 3:
                        logger.warning("crawl_stopped_consecutive_empty", pages=page)
                        break
                    continue

                consecutive_empty = 0
                self._stats["total_fetched"] += result.items_fetched
                self._stats["total_new"] += result.items_new
                self._stats["total_updated"] += result.items_updated

                if result.items_fetched == 0:
                    logger.info("crawl_page_empty", page=page)
                    break

                logger.info(
                    "crawl_page_completed",
                    page=page,
                    items=result.items_fetched,
                    new=result.items_new,
                    updated=result.items_updated,
                )

                yield result

                page += 1

    async def crawl_incremental(self, days: int = 1) -> CrawlResult[T]:
        """
        增量爬取 - 只爬取指定天数内的新数据

        Args:
            days: 距今天数

        Returns:
            CrawlResult: 爬取结果
        """
        from ..utils.time_utils import get_date_range

        start_date, end_date = get_date_range(days)
        logger.info("incremental_crawl_started", start_date=start_date, end_date=end_date)

        total_items = 0
        total_new = 0
        total_updated = 0
        all_errors = []

        async for result in self.crawl_paginated(max_pages=1000):
            total_items += result.items_fetched
            total_new += result.items_new
            total_updated += result.items_updated
            all_errors.extend(result.errors)

            # 检查是否超出日期范围
            if result.data and result.data[-1].publish_date < start_date:
                break

        return CrawlResult(
            success=len(all_errors) == 0,
            items_fetched=total_items,
            items_new=total_new,
            items_updated=total_updated,
            errors=all_errors,
        )

    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = {
            "total_fetched": 0,
            "total_new": 0,
            "total_updated": 0,
            "total_errors": 0,
        }
