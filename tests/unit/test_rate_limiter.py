"""
限流器单元测试
"""

import asyncio
import time

import pytest

from src.core.rate_limiter import (
    InMemoryRateLimiter,
    RateLimitConfig,
    TokenBucketRateLimiter,
    create_rate_limiter,
)


class TestInMemoryRateLimiter:
    """内存限流器测试"""

    @pytest.mark.asyncio
    async def test_acquire(self) -> None:
        """测试获取许可"""
        limiter = InMemoryRateLimiter(rate=10.0, burst=10)

        # 应该能立即获取
        await limiter.acquire()
        assert limiter.available is True

    @pytest.mark.asyncio
    async def test_rate_limiting(self) -> None:
        """测试限流"""
        limiter = InMemoryRateLimiter(rate=2.0, burst=2)

        # 前两个应该立即获取
        await limiter.acquire()
        await limiter.acquire()

        # 第三个应该需要等待
        start = time.time()
        await limiter.acquire()
        elapsed = time.time() - start

        # 应该等待了大约0.5秒（1/2 = 0.5）
        assert elapsed >= 0.4

    @pytest.mark.asyncio
    async def test_burst_capacity(self) -> None:
        """测试突发容量"""
        limiter = InMemoryRateLimiter(rate=1.0, burst=5)

        # 快速获取5个许可
        for _ in range(5):
            await limiter.acquire()

        # tokens应该耗尽
        assert limiter.tokens < 1

    @pytest.mark.asyncio
    async def test_rate_limiting_effect(self) -> None:
        """测试限流效果 - 验证连续请求之间有延迟"""
        limiter = InMemoryRateLimiter(rate=5.0, burst=5)

        # 消耗突发容量
        for _ in range(5):
            await limiter.acquire()

        # 下一个请求应该触发限流等待
        start = time.time()
        await limiter.acquire()
        elapsed = time.time() - start

        # 应该等待了至少0.1秒（rate=5，即0.2秒/请求）
        assert elapsed >= 0.15


class TestTokenBucketRateLimiter:
    """令牌桶限流器测试"""

    @pytest.mark.asyncio
    async def test_acquire_single_token(self) -> None:
        """测试获取单个令牌"""
        limiter = TokenBucketRateLimiter(rate=10, capacity=10)

        # 应该能立即获取
        await limiter.acquire(1)

    @pytest.mark.asyncio
    async def test_bucket_capacity(self) -> None:
        """测试桶容量"""
        limiter = TokenBucketRateLimiter(rate=1, capacity=3)

        # 填满桶
        await limiter.acquire(3)

        # 再次获取需要等待
        start = time.time()
        await limiter.acquire(1)
        elapsed = time.time() - start

        # 应该等待了大约1秒
        assert elapsed >= 0.9

    @pytest.mark.asyncio
    async def test_rate_governance(self) -> None:
        """测试速率控制"""
        limiter = TokenBucketRateLimiter(rate=5, capacity=5)

        # 耗尽桶
        await limiter.acquire(5)

        # 等待补充一些
        await asyncio.sleep(1.0)  # 补充5个tokens

        # 应该能获取
        start = time.time()
        await limiter.acquire(5)
        elapsed = time.time() - start

        # 不应该等待太久（因为已补充）
        assert elapsed < 0.5


class TestRateLimiterFactory:
    """限流器工厂测试"""

    def test_create_memory_limiter(self) -> None:
        """测试创建内存限流器"""
        config = RateLimitConfig(backend="memory", rate=60.0, burst=60)
        limiter = create_rate_limiter(config)

        assert isinstance(limiter, InMemoryRateLimiter)

    def test_create_token_bucket_limiter(self) -> None:
        """测试创建令牌桶限流器"""
        config = RateLimitConfig(backend="token_bucket", rate=60.0, burst=60)
        limiter = create_rate_limiter(config)

        assert isinstance(limiter, TokenBucketRateLimiter)
