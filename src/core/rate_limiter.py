"""
限流器 - 支持内存和Redis两种实现
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Protocol

from ..utils.logger import get_logger

logger = get_logger(__name__)


class RateLimiterBackend(Protocol):
    """限流器后端协议"""

    async def acquire(self) -> None:
        """获取许可"""
        ...

    async def release(self) -> None:
        """释放许可"""
        ...

    @property
    def available(self) -> bool:
        """是否有可用许可"""
        ...


class InMemoryRateLimiter:
    """
    内存限流器 - 基于滑动窗口算法

    Args:
        rate: 每秒允许的请求数
        burst: 突发容量
    """

    def __init__(self, rate: float = 10.0, burst: int = 20) -> None:
        self._rate = rate
        self._burst = burst
        self._tokens = float(burst)
        self._last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """获取许可，必要时等待"""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_update
            self._last_update = now

            # 补充tokens
            self._tokens = min(self._burst, self._tokens + elapsed * self._rate)

            if self._tokens < 1:
                # 需要等待
                wait_time = (1 - self._tokens) / self._rate
                logger.debug("rate_limit_wait", wait_seconds=wait_time)
                await asyncio.sleep(wait_time)
                self._tokens = 0
            else:
                self._tokens -= 1

    def release(self) -> None:
        """释放许可（当前实现不需要）"""
        pass

    @property
    def available(self) -> bool:
        """是否有可用许可"""
        return self._tokens >= 1

    @property
    def tokens(self) -> float:
        """当前可用token数"""
        return self._tokens


class TokenBucketRateLimiter:
    """
    令牌桶限流器

    Args:
        rate: 每秒添加的令牌数
        capacity: 桶容量
    """

    def __init__(self, rate: float = 60, capacity: int = 60) -> None:
        self._rate = rate
        self._capacity = capacity
        self._tokens = float(capacity)
        self._last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> None:
        """获取指定数量的令牌"""
        async with self._lock:
            await self._refill()

            if self._tokens < tokens:
                # 计算需要等待的时间
                needed = tokens - self._tokens
                wait_time = needed / self._rate
                logger.debug("token_bucket_wait", wait_seconds=wait_time, needed=needed)
                await asyncio.sleep(wait_time)
                await self._refill()

            self._tokens -= tokens

    async def _refill(self) -> None:
        """补充令牌"""
        now = time.monotonic()
        elapsed = now - self._last_update
        self._last_update = now

        self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)

    def release(self) -> None:
        """释放令牌（令牌桶不支持）"""
        pass

    @property
    def available(self) -> bool:
        """是否有可用令牌"""
        return self._tokens >= 1


class RedisRateLimiter:
    """
    Redis限流器 - 基于滑动窗口算法

    Args:
        redis_client: Redis客户端
        key: 限流器键名
        rate: 每秒允许的请求数
        window: 窗口大小（秒）
    """

    def __init__(
        self,
        redis_client: object,
        key: str = "rate_limit",
        rate: float = 60.0,
        window: int = 60,
    ) -> None:
        import redis.asyncio as redis

        self._redis: redis.Redis = redis_client  # type: ignore
        self._key = key
        self._rate = rate
        self._window = window

    async def acquire(self) -> None:
        """获取许可"""

        now = time.time()
        window_start = now - self._window

        pipe = self._redis.pipeline()
        # 移除窗口外的记录
        pipe.zremrangebyscore(self._key, 0, window_start)
        # 获取当前窗口内的请求数
        pipe.zcard(self._key)
        # 添加当前请求
        pipe.zadd(self._key, {str(now): now})
        # 设置过期时间
        pipe.expire(self._key, self._window + 1)

        results = await pipe.execute()
        current_count = results[1]

        if current_count >= self._rate:
            # 超出限制，等待
            oldest = await self._redis.zrange(self._key, 0, 0, withscores=True)
            if oldest:
                wait_time = oldest[0][1] + self._window - now
                if wait_time > 0:
                    logger.debug("redis_rate_limit_wait", wait_seconds=wait_time)
                    await asyncio.sleep(wait_time)

        logger.debug("redis_rate_limit_acquired", current_count=current_count + 1)

    async def release(self) -> None:
        """释放许可（可选，用于清理）"""
        pass

    @property
    def available(self) -> bool:
        """检查是否有可用许可"""
        # 同步方法，不适合异步上下文
        return True


@dataclass
class RateLimitConfig:
    """限流配置"""

    backend: str = "memory"  # "memory" or "redis"
    rate: float = 60.0  # 每秒/每分钟请求数
    burst: int = 20  # 突发容量


def create_rate_limiter(
    config: RateLimitConfig, redis_client: object | None = None
) -> RateLimiterBackend:
    """
    创建限流器实例

    Args:
        config: 限流配置
        redis_client: Redis客户端（可选）

    Returns:
        RateLimiterBackend: 限流器实例
    """
    if config.backend == "redis" and redis_client:
        return RedisRateLimiter(
            redis_client=redis_client,
            rate=config.rate,
            window=60,
        )
    elif config.backend == "token_bucket":
        return TokenBucketRateLimiter(rate=config.rate, capacity=config.burst)
    else:
        return InMemoryRateLimiter(rate=config.rate, burst=config.burst)
