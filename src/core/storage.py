"""
数据存储抽象层 - Repository模式
"""
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Generic, TypeVar

from ..models.announcement import Announcement, AnnouncementCreate, AnnouncementUpdate
from ..utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound=Announcement)


class BaseRepository(ABC, Generic[T]):
    """数据访问基类"""

    @abstractmethod
    async def create(self, entity: AnnouncementCreate) -> T:
        """创建记录"""
        pass

    @abstractmethod
    async def get_by_id(self, id: str) -> T | None:
        """根据ID获取记录"""
        pass

    @abstractmethod
    async def get_by_hash(self, content_hash: str) -> T | None:
        """根据内容哈希获取记录"""
        pass

    @abstractmethod
    async def update(self, id: str, entity: AnnouncementUpdate) -> T | None:
        """更新记录"""
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """删除记录"""
        pass

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        announcement_type: str | None = None,
        category: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[T]:
        """获取列表"""
        pass

    @abstractmethod
    async def count(
        self,
        announcement_type: str | None = None,
        category: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> int:
        """获取总数"""
        pass

    @abstractmethod
    async def exists(self, content_hash: str) -> bool:
        """检查记录是否存在"""
        pass


class InMemoryRepository(BaseRepository[T]):
    """内存存储实现（用于测试）"""

    def __init__(self) -> None:
        self._store: dict[str, T] = {}
        self._hash_index: dict[str, str] = {}  # hash -> id

    async def create(self, entity: Announcement | AnnouncementCreate) -> T:
        """创建记录"""
        # 如果传入的是已构建的Announcement对象，直接使用
        if isinstance(entity, Announcement):
            announcement = entity
        else:
            # 否则从AnnouncementCreate构建
            announcement = Announcement(
                id=self._generate_id(),
                title=entity.title,
                announcement_type=entity.announcement_type,
                category=entity.category,
                publish_date=entity.publish_date,
                deadline=entity.deadline,
                url=entity.url,
                content_hash=Announcement.compute_hash(entity.raw_content or entity.title),
                raw_content=entity.raw_content,
                org_name=entity.org_name,
                contact_info=entity.contact_info,
            )

        self._store[announcement.id] = announcement
        self._hash_index[announcement.content_hash] = announcement.id

        logger.info("announcement_created", id=announcement.id, title=announcement.title)
        return announcement

    async def get_by_id(self, id: str) -> T | None:
        """根据ID获取记录"""
        return self._store.get(id)

    async def get_by_hash(self, content_hash: str) -> T | None:
        """根据内容哈希获取记录"""
        id = self._hash_index.get(content_hash)
        if id:
            return self._store.get(id)
        return None

    async def update(self, id: str, entity: Announcement | AnnouncementUpdate) -> T | None:
        """更新记录"""
        existing = self._store.get(id)
        if not existing:
            return None

        # 如果传入的是完整的Announcement对象，替换整个记录
        if isinstance(entity, Announcement):
            entity.updated_at = datetime.now(timezone.utc)
            self._store[id] = entity
            logger.info("announcement_updated", id=id)
            return entity

        # 否则按字段更新
        update_data = entity.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                setattr(existing, key, value)

        existing.updated_at = datetime.now(timezone.utc)
        self._store[id] = existing

        logger.info("announcement_updated", id=id)
        return existing

    async def delete(self, id: str) -> bool:
        """删除记录"""
        existing = self._store.pop(id, None)
        if existing:
            self._hash_index.pop(existing.content_hash, None)
            logger.info("announcement_deleted", id=id)
            return True
        return False

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        announcement_type: str | None = None,
        category: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[T]:
        """获取列表"""
        results = list(self._store.values())

        # 过滤
        if announcement_type:
            results = [r for r in results if r.announcement_type == announcement_type]
        if category:
            results = [r for r in results if r.category == category]
        if start_date:
            results = [r for r in results if r.publish_date >= start_date]
        if end_date:
            results = [r for r in results if r.publish_date <= end_date]

        # 排序
        results.sort(key=lambda x: x.publish_date, reverse=True)

        # 分页
        return results[skip : skip + limit]

    async def count(
        self,
        announcement_type: str | None = None,
        category: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> int:
        """获取总数"""
        items = await self.list(
            skip=0,
            limit=1000000,
            announcement_type=announcement_type,
            category=category,
            start_date=start_date,
            end_date=end_date,
        )
        return len(items)

    async def exists(self, content_hash: str) -> bool:
        """检查记录是否存在"""
        return content_hash in self._hash_index

    def _generate_id(self) -> str:
        """生成ID"""
        import uuid
        return str(uuid.uuid4())


class SQLAlchemyRepository(BaseRepository[T]):
    """SQLAlchemy ORM实现（待生产使用）"""

    def __init__(self, session: object) -> None:
        self._session = session  # sqlalchemy.ext.asyncio.AsyncSession

    async def create(self, entity: AnnouncementCreate) -> T:
        """创建记录"""
        # TODO: 实现SQLAlchemy创建逻辑
        raise NotImplementedError("SQLAlchemyRepository.create not implemented")

    async def get_by_id(self, id: str) -> T | None:
        """根据ID获取记录"""
        raise NotImplementedError("SQLAlchemyRepository.get_by_id not implemented")

    async def get_by_hash(self, content_hash: str) -> T | None:
        """根据内容哈希获取记录"""
        raise NotImplementedError("SQLAlchemyRepository.get_by_hash not implemented")

    async def update(self, id: str, entity: AnnouncementUpdate) -> T | None:
        """更新记录"""
        raise NotImplementedError("SQLAlchemyRepository.update not implemented")

    async def delete(self, id: str) -> bool:
        """删除记录"""
        raise NotImplementedError("SQLAlchemyRepository.delete not implemented")

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        announcement_type: str | None = None,
        category: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[T]:
        """获取列表"""
        raise NotImplementedError("SQLAlchemyRepository.list not implemented")

    async def count(
        self,
        announcement_type: str | None = None,
        category: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> int:
        """获取总数"""
        raise NotImplementedError("SQLAlchemyRepository.count not implemented")

    async def exists(self, content_hash: str) -> bool:
        """检查记录是否存在"""
        raise NotImplementedError("SQLAlchemyRepository.exists not implemented")
