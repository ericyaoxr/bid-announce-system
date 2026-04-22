"""
去重管道 - 基于内容哈希
"""

import hashlib
from typing import TypedDict

from ..models.announcement import Announcement
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DeduplicationResult(TypedDict):
    """去重结果"""

    is_duplicate: bool
    original_id: str | None
    hash: str


class DeduplicationPipeline:
    """去重管道"""

    def __init__(self) -> None:
        self._hash_cache: set[str] = set()

    def compute_hash(self, announcement: Announcement) -> str:
        """
        计算公告内容的哈希值

        Args:
            announcement: 公告对象

        Returns:
            str: SHA256哈希值
        """
        # 使用关键字段组合计算哈希
        content_parts = [
            announcement.title,
            str(announcement.publish_date.date() if announcement.publish_date else ""),
            str(announcement.announcement_type),
            str(announcement.category),
        ]

        # 如果有原始内容，也加入哈希计算
        if announcement.raw_content:
            content_parts.append(announcement.raw_content[:500])  # 只取前500字符

        content = "|".join(content_parts)
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    async def execute(self, announcement: Announcement) -> DeduplicationResult:
        """
        执行去重检查

        Args:
            announcement: 待检查的公告对象

        Returns:
            DeduplicationResult: 去重结果
        """
        content_hash = self.compute_hash(announcement)
        announcement.content_hash = content_hash

        # 检查是否在缓存中
        if content_hash in self._hash_cache:
            logger.info("duplicate_detected", hash=content_hash, title=announcement.title)
            return DeduplicationResult(
                is_duplicate=True,
                original_id=None,  # 需要外部存储来追踪原始ID
                hash=content_hash,
            )

        # 添加到缓存
        self._hash_cache.add(content_hash)
        logger.debug("hash_added", hash=content_hash, title=announcement.title)

        return DeduplicationResult(
            is_duplicate=False,
            original_id=None,
            hash=content_hash,
        )

    def clear_cache(self) -> None:
        """清空缓存"""
        self._hash_cache.clear()
        logger.info("deduplication_cache_cleared")

    def load_from_storage(self, existing_hashes: set[str]) -> None:
        """
        从存储加载已有哈希

        Args:
            existing_hashes: 已存在的哈希集合
        """
        self._hash_cache = existing_hashes
        logger.info("deduplication_cache_loaded", count=len(existing_hashes))

    @property
    def cache_size(self) -> int:
        """缓存大小"""
        return len(self._hash_cache)
