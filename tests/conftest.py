"""
测试配置文件 - pytest fixtures
"""

import asyncio
from collections.abc import AsyncGenerator, Generator
from datetime import UTC, datetime

import pytest

from src.config.settings import Settings, get_settings
from src.core.fetcher import AsyncFetcher, Fetcher, FetcherConfig
from src.core.parser import JSONParser, ListPageParser
from src.core.rate_limiter import InMemoryRateLimiter, TokenBucketRateLimiter
from src.core.scheduler import JobScheduler
from src.core.storage import InMemoryRepository
from src.models.announcement import Announcement, AnnouncementCreate


@pytest.fixture
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """创建事件循环"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def fetcher_config() -> FetcherConfig:
    """HTTP客户端配置"""
    return FetcherConfig(
        timeout=30.0,
        max_retries=3,
        user_agent="TestAgent/1.0",
    )


@pytest.fixture
def fetcher(fetcher_config: FetcherConfig) -> Generator[Fetcher, None, None]:
    """同步HTTP客户端"""
    with Fetcher(fetcher_config) as f:
        yield f


@pytest.fixture
async def async_fetcher(fetcher_config: FetcherConfig) -> AsyncGenerator[AsyncFetcher, None]:
    """异步HTTP客户端"""
    async with AsyncFetcher(fetcher_config) as f:
        yield f


@pytest.fixture
def list_parser() -> ListPageParser:
    """列表页解析器"""
    return ListPageParser(
        selectors={
            "item_container": ".item",
            "title": "a::text",
            "date": "::attr(data-time)",
            "type": ".type::text",
            "category": ".category::text",
            "detail_link": "a::attr(href)",
            "page_info": ".pagination::text",
        }
    )


@pytest.fixture
def json_parser() -> JSONParser:
    """JSON解析器"""
    return JSONParser(selectors={})


@pytest.fixture
def rate_limiter() -> InMemoryRateLimiter:
    """内存限流器"""
    return InMemoryRateLimiter(rate=10.0, burst=20)


@pytest.fixture
def token_bucket_limiter() -> TokenBucketRateLimiter:
    """令牌桶限流器"""
    return TokenBucketRateLimiter(rate=60, capacity=60)


@pytest.fixture
def repository() -> InMemoryRepository[Announcement]:
    """内存存储"""
    return InMemoryRepository[Announcement]()


@pytest.fixture
def sample_announcement_data() -> dict:
    """示例公告数据"""
    return {
        "id": "test-123",
        "title": "测试采购公告",
        "announcement_type": "采购公告",
        "category": "货物",
        "publish_date": datetime.now(UTC),
        "url": "https://example.com/announcement/123",
        "content_hash": "abc123",
    }


@pytest.fixture
def sample_announcement_create() -> AnnouncementCreate:
    """示例公告创建数据"""
    return AnnouncementCreate(
        title="测试采购公告",
        announcement_type="采购公告",
        category="货物",
        publish_date=datetime.now(UTC),
        url="https://example.com/announcement/123",
    )


@pytest.fixture
def crawler_config() -> dict:
    """采集数据配置"""
    return {
        "target_url": "https://zcpt.szcg.cn/api/v1/announcements",
        "max_retries": 3,
        "timeout": 30.0,
        "rate_limit_rpm": 60,
        "batch_size": 50,
    }


@pytest.fixture
def job_scheduler() -> JobScheduler:
    """任务调度器"""
    return JobScheduler()


@pytest.fixture
def settings() -> Settings:
    """应用配置"""
    return get_settings()
