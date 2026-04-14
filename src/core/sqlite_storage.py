"""
SQLite持久化存储实现
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..models.announcement import Announcement, AnnouncementCreate
from ..utils.logger import get_logger

logger = get_logger(__name__)


class SQLiteRepository:
    """SQLite持久化存储"""

    def __init__(self, db_path: str = "data/announcements.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS announcements (
                    id TEXT PRIMARY KEY,
                    project_id INTEGER,
                    project_no TEXT NOT NULL,
                    title TEXT NOT NULL,
                    announcement_type INTEGER DEFAULT 1,
                    tender_mode TEXT,
                    tender_mode_desc TEXT,
                    project_type_code TEXT,
                    current_status INTEGER,
                    project_source INTEGER,
                    category TEXT,
                    publish_date TEXT,
                    deadline TEXT,
                    url TEXT NOT NULL,
                    source TEXT DEFAULT 'zcpt.szcg.cn',
                    content_hash TEXT NOT NULL,
                    raw_content TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_content_hash ON announcements(content_hash)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_publish_date ON announcements(publish_date)
            """)
            logger.info("database_initialized", db_path=str(self.db_path))

    async def create(self, announcement: Announcement) -> Announcement:
        """创建记录"""
        self.save(announcement)
        return announcement

    async def get_by_id(self, id: str) -> Announcement | None:
        """根据ID获取记录"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM announcements WHERE id = ?",
                (id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_announcement(dict(row))
            return None

    async def get_by_hash(self, content_hash: str) -> Announcement | None:
        """根据内容哈希获取记录"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM announcements WHERE content_hash = ?",
                (content_hash,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_announcement(dict(row))
            return None

    async def update(self, id: str, announcement: Announcement) -> Announcement | None:
        """更新记录"""
        existing = await self.get_by_id(id)
        if existing is None:
            return None
        self.save(announcement)
        return announcement

    async def delete(self, id: str) -> bool:
        """删除记录"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM announcements WHERE id = ?", (id,))
            return cursor.rowcount > 0

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        announcement_type: str | None = None,
        category: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[Announcement]:
        """获取列表"""
        data = self.list_all(limit=limit, offset=skip)
        return [self._row_to_announcement(row) for row in data]

    async def count(
        self,
        announcement_type: str | None = None,
        category: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> int:
        """获取总数"""
        return self.count()

    async def exists(self, content_hash: str) -> bool:
        """检查记录是否存在"""
        return self.exists(content_hash)

    def _row_to_announcement(self, row: dict[str, Any]) -> Announcement:
        """将数据库行转换为Announcement对象"""
        return Announcement(
            id=str(row["id"]),
            project_id=row.get("project_id"),
            project_no=row.get("project_no", ""),
            title=row.get("title", ""),
            announcement_type=row.get("announcement_type", 1),
            tender_mode=row.get("tender_mode", ""),
            tender_mode_desc=row.get("tender_mode_desc", ""),
            project_type_code=row.get("project_type_code"),
            current_status=row.get("current_status"),
            project_source=row.get("project_source"),
            category=row.get("category", ""),
            publish_date=datetime.fromisoformat(row["publish_date"]) if row.get("publish_date") else datetime.now(timezone.utc),
            deadline=datetime.fromisoformat(row["deadline"]) if row.get("deadline") else None,
            url=row.get("url", ""),
            source=row.get("source", "zcpt.szcg.cn"),
            content_hash=row.get("content_hash", ""),
            raw_content=row.get("raw_content"),
            created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(row["updated_at"]) if row.get("updated_at") else datetime.now(timezone.utc),
        )

    def save(self, announcement: Announcement) -> None:
        """保存公告到数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO announcements
                (id, project_id, project_no, title, announcement_type, tender_mode,
                 tender_mode_desc, project_type_code, current_status, project_source,
                 category, publish_date, deadline, url, source, content_hash,
                 raw_content, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                announcement.id,
                announcement.project_id,
                announcement.project_no,
                announcement.title,
                announcement.announcement_type,
                announcement.tender_mode,
                announcement.tender_mode_desc,
                announcement.project_type_code,
                announcement.current_status,
                announcement.project_source,
                announcement.category,
                announcement.publish_date.isoformat() if announcement.publish_date else None,
                announcement.deadline.isoformat() if announcement.deadline else None,
                str(announcement.url),
                announcement.source,
                announcement.content_hash,
                announcement.raw_content,
                announcement.created_at.isoformat() if announcement.created_at else datetime.now(timezone.utc).isoformat(),
                announcement.updated_at.isoformat() if announcement.updated_at else datetime.now(timezone.utc).isoformat(),
            ))
        logger.debug("announcement_saved", id=announcement.id, title=announcement.title)

    def exists(self, content_hash: str) -> bool:
        """检查内容哈希是否存在"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM announcements WHERE content_hash = ? LIMIT 1",
                (content_hash,)
            )
            return cursor.fetchone() is not None

    def count(self) -> int:
        """获取总数"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM announcements")
            return cursor.fetchone()[0]

    def list_all(self, limit: int = 1000, offset: int = 0) -> list[dict[str, Any]]:
        """获取所有公告"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM announcements ORDER BY publish_date DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
            return [dict(row) for row in cursor.fetchall()]

    def export_to_json(self, filepath: str = "data/announcements.json") -> None:
        """导出到JSON文件"""
        data = self.list_all(limit=1000000)
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("data_exported", count=len(data), filepath=filepath)

    def export_to_csv(self, filepath: str = "data/announcements.csv") -> None:
        """导出到CSV文件"""
        import csv
        data = self.list_all(limit=1000000)
        if not data:
            return
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        logger.info("data_exported", count=len(data), filepath=filepath)

    def get_by_id_sync(self, id: str) -> dict[str, Any] | None:
        """同步根据ID获取记录（返回字典）"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM announcements WHERE id = ?",
                (id,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None