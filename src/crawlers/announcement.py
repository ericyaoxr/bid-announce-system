"""
招标公告采集 - 适配采购平台API
"""

import asyncio
import time
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from src.config.settings import Settings, get_settings
from src.config.urls import build_list_url
from src.core.fetcher import AsyncFetcher, FetcherConfig
from src.core.parser import ListPageParser, ParseResult
from src.core.rate_limiter import InMemoryRateLimiter
from src.core.storage import BaseRepository, InMemoryRepository
from src.models.announcement import Announcement
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CrawlResult:
    """抓取结果"""

    success: bool
    items_fetched: int = 0
    items_new: int = 0
    items_updated: int = 0
    errors: list[str] = field(default_factory=list)
    duration_ms: int = 0
    page: int | None = None
    total_pages: int | None = None
    total_records: int | None = None


@dataclass
class CrawlerConfig:
    """采集数据配置"""

    target_url: str
    max_retries: int = 3
    timeout: float = 30.0
    rate_limit_rpm: int = 60
    batch_size: int = 20
    base_url: str = "https://zcpt.szcg.cn"


class AnnouncementCrawler:
    """
    招标公告采集数据

    API端点: /group-tendering-website/officialwebsite/project/page
    参数:
        - announcementType: 公告类型 (1=采购公告, 2=变更公告等)
        - current: 页码
        - size: 每页条数
    """

    def __init__(
        self,
        fetcher: AsyncFetcher,
        parser: ListPageParser,
        rate_limiter: InMemoryRateLimiter,
        repository: BaseRepository[Announcement],
        config: CrawlerConfig,
    ) -> None:
        self._fetcher = fetcher
        self._parser = parser
        self._rate_limiter = rate_limiter
        self._repository = repository
        self._config = config
        self._client_initialized = False

    async def _ensure_client(self) -> None:
        """确保异步客户端已初始化"""
        if not self._client_initialized and hasattr(self._fetcher, "__aenter__"):
            await self._fetcher.__aenter__()
            self._client_initialized = True

    async def close(self) -> None:
        """关闭采集数据及相关资源"""
        if self._client_initialized and hasattr(self._fetcher, "__aexit__"):
            await self._fetcher.__aexit__(None, None, None)
            self._client_initialized = False

    async def crawl_page(
        self, page: int, announcement_type: int = 1
    ) -> tuple[ParseResult, list[Announcement]]:
        """
        抓取单页数据

        Args:
            page: 页码
            announcement_type: 公告类型

        Returns:
            (解析结果, 公告列表)
        """
        # 确保客户端已初始化
        await self._ensure_client()

        url = build_list_url(
            base_url=self._config.base_url + "/group-tendering-website",
            announcement_type=announcement_type,
            current=page,
            size=self._config.batch_size,
        )

        # 限流
        await self._rate_limiter.acquire()

        # 抓取
        logger.info("crawling_page", page=page, url=url)
        response = await self._fetcher.get(url)

        # 解析
        announcements, errors = self._parser.parse_to_announcements(
            response.content, base_url=self._config.base_url
        )

        if errors:
            logger.warning("parse_warnings", page=page, errors=errors)

        result = self._parser.parse(response.content)
        return result, announcements

    async def crawl_paginated(
        self,
        start_page: int = 1,
        max_pages: int = 100,
        announcement_type: int = 1,
    ) -> AsyncGenerator[CrawlResult, None]:
        """
        分页抓取

        Args:
            start_page: 起始页
            max_pages: 最大页数
            announcement_type: 公告类型

        Yields:
            每页的抓取结果
        """
        current_page = start_page

        while current_page <= max_pages:
            start_time = time.time()

            try:
                result, announcements = await self.crawl_page(current_page, announcement_type)

                if not result.success:
                    yield CrawlResult(
                        success=False,
                        errors=result.errors,
                        page=current_page,
                    )
                    current_page += 1
                    continue

                # 存储并去重
                items_new = 0
                items_updated = 0

                for announcement in announcements:
                    existing = await self._repository.get_by_id(announcement.id)
                    if existing is None:
                        await self._repository.create(announcement)
                        items_new += 1
                    else:
                        await self._repository.update(announcement)
                        items_updated += 1

                duration_ms = int((time.time() - start_time) * 1000)

                yield CrawlResult(
                    success=True,
                    items_fetched=len(announcements),
                    items_new=items_new,
                    items_updated=items_updated,
                    duration_ms=duration_ms,
                    page=current_page,
                    total_pages=result.total_pages,
                    total_records=result.total,
                )

                # 检查是否到达最后一页
                if result.total_pages and current_page >= result.total_pages:
                    logger.info("reached_last_page", page=current_page)
                    break

                current_page += 1

                # 避免请求过快
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error("crawl_error", page=current_page, error=str(e))
                yield CrawlResult(
                    success=False,
                    errors=[str(e)],
                    page=current_page,
                )
                current_page += 1

    async def crawl_incremental(self, days: int = 1) -> CrawlResult:
        """
        增量抓取 - 只抓取最近N天的数据

        Args:
            days: 抓取最近N天的数据

        Returns:
            抓取结果汇总
        """
        start_time = time.time()
        total_fetched = 0
        total_new = 0
        total_updated = 0
        _errors: list[str] = []  # TODO: 收集错误信息

        cutoff_date = datetime.now(UTC) - timedelta(days=days)

        logger.info("starting_incremental_crawl", days=days, cutoff_date=cutoff_date.isoformat())

        # 抓取首页获取总页数
        result, _ = await self.crawl_page(1)
        if not result.success:
            return CrawlResult(
                success=False,
                errors=result.errors,
                duration_ms=int((time.time() - start_time) * 1000),
            )

        max_pages = result.total_pages or 1

        # 逐页抓取直到超过日期范围
        for page in range(1, max_pages + 1):
            _, announcements = await self.crawl_page(page)

            page_old_count = 0
            for announcement in announcements:
                if announcement.publish_date < cutoff_date:
                    page_old_count += 1
                    continue

                existing = await self._repository.get_by_id(announcement.id)
                if existing is None:
                    await self._repository.create(announcement)
                    total_new += 1
                else:
                    await self._repository.update(announcement)
                    total_updated += 1

                total_fetched += 1

            # 如果当前页超过一半是旧数据，停止抓取
            if page_old_count > len(announcements) // 2:
                logger.info("passed_cutoff_date", page=page)
                break

        return CrawlResult(
            success=True,
            items_fetched=total_fetched,
            items_new=total_new,
            items_updated=total_updated,
            duration_ms=int((time.time() - start_time) * 1000),
        )


def create_announcement_crawler(
    target_url: str | None = None,
    rate_limit_rpm: int = 60,
    settings: Settings | None = None,
    use_sqlite: bool = False,
    db_path: str = "data/announcements.db",
) -> AnnouncementCrawler:
    """
    创建公告采集数据实例

    Args:
        target_url: 目标URL（可选，默认使用配置）
        rate_limit_rpm: 每分钟请求数限制
        settings: 配置对象
        use_sqlite: 是否使用SQLite持久化存储
        db_path: SQLite数据库路径

    Returns:
        AnnouncementCrawler实例
    """
    settings = settings or get_settings()

    # 采集数据配置
    config = CrawlerConfig(
        target_url=target_url
        or f"{settings.target_base_url}/group-tendering-website/officialwebsite/project/page",
        rate_limit_rpm=rate_limit_rpm,
        batch_size=settings.crawler_batch_size,
        base_url=settings.target_base_url,
    )

    # HTTP客户端
    fetcher_config = FetcherConfig(
        timeout=30.0,
        max_retries=3,
    )
    fetcher = AsyncFetcher(fetcher_config)

    # 解析器
    parser = ListPageParser()

    # 限流器
    rate_limiter = InMemoryRateLimiter(rate=float(rate_limit_rpm) / 60.0, burst=rate_limit_rpm)

    # 存储
    if use_sqlite:
        from src.core.sqlite_storage import SQLiteRepository

        repository = SQLiteRepository(db_path=db_path)
    else:
        repository: BaseRepository[Announcement] = InMemoryRepository()

    return AnnouncementCrawler(
        fetcher=fetcher,
        parser=parser,
        rate_limiter=rate_limiter,
        repository=repository,
        config=config,
    )
