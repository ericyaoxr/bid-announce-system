"""
招标公告数据模型 - 适配采购平台API
"""
import hashlib
from datetime import UTC, datetime
from typing import Any, Self

from pydantic import BaseModel, Field, HttpUrl, field_validator


class TenderProjectBase(BaseModel):
    """招标项目基础模型"""
    project_id: int | None = Field(None, description="项目ID")
    project_no: str = Field(..., description="项目编号")
    tender_mode: str = Field(..., description="招标方式代码")
    tender_mode_desc: str = Field(..., description="招标方式描述")
    project_type_code: str | None = Field(None, description="招标项目类型代码")
    current_status: int | None = Field(None, description="当前状态代码")
    project_source: int | None = Field(None, description="项目来源")


class Announcement(TenderProjectBase):
    """
    招标公告完整模型

    对应API响应字段:
    - announcementId -> id
    - announcementName -> title
    - tenderProjectTypeDesc -> category
    - releaseTime -> publish_date
    - releaseEndTime -> deadline
    """
    id: str = Field(..., description="公告ID（唯一标识）")
    title: str = Field(..., min_length=1, max_length=500, description="公告名称")
    announcement_type: int = Field(default=1, description="公告类型 (1=采购公告)")
    category: str = Field(..., description="招标项目类型描述（工程类/货物类/服务类）")
    publish_date: datetime = Field(..., description="发布时间")
    deadline: datetime | None = Field(None, description="发布截止时间")
    url: HttpUrl = Field(..., description="公告URL")
    source: str = Field(default="zcpt.szcg.cn", description="数据来源")
    content_hash: str = Field(..., description="内容哈希（用于去重）")
    raw_content: str | None = Field(None, description="原始JSON内容")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, v: Any) -> str:
        """标准化类别名称"""
        if v is None:
            return "未知"
        mapping = {"货物类": "货物", "工程类": "工程", "服务类": "服务"}
        return mapping.get(v, v)

    @staticmethod
    def compute_hash(content: str) -> str:
        """计算内容哈希用于去重"""
        return hashlib.sha256(content.encode()).hexdigest()

    def compute_self_hash(self) -> str:
        """计算自身内容的哈希"""
        content = f"{self.id}:{self.title}:{self.publish_date.isoformat()}"
        return self.compute_hash(content)

    @property
    def is_expired(self) -> bool:
        """判断是否已过期"""
        if self.deadline is None:
            return False
        return datetime.now(UTC) > self.deadline

    @property
    def days_until_deadline(self) -> int | None:
        """距离截止日期天数"""
        if self.deadline is None:
            return None
        delta = self.deadline - datetime.now(UTC)
        return delta.days

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "project_no": self.project_no,
            "title": self.title,
            "tender_mode": self.tender_mode,
            "tender_mode_desc": self.tender_mode_desc,
            "category": self.category,
            "publish_date": self.publish_date.isoformat() if self.publish_date else None,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "url": str(self.url),
            "source": self.source,
            "status_code": self.current_status,
            "is_expired": self.is_expired,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_api_response(cls, data: dict[str, Any], base_url: str) -> Self:
        """从API响应创建模型"""
        release_time = data.get("releaseTime")
        publish_date = datetime.fromisoformat(release_time) if release_time else datetime.now(timezone.utc)

        release_end_time = data.get("releaseEndTime")
        deadline = datetime.fromisoformat(release_end_time) if release_end_time else None

        announcement_id = data.get("announcementId", "")
        url = f"{base_url}/group-tendering-website/officialwebsite/project/detail/{announcement_id}"

        instance = cls(
            id=str(announcement_id),
            project_id=data.get("projectId"),
            project_no=data.get("projectNo", ""),
            title=data.get("announcementName", ""),
            tender_mode=data.get("tenderMode", ""),
            tender_mode_desc=data.get("tenderModeDesc", "未知"),
            project_type_code=data.get("tenderProjectType"),
            category=data.get("tenderProjectTypeDesc", "未知"),
            publish_date=publish_date,
            deadline=deadline,
            url=url,
            current_status=data.get("currentStatus"),
            project_source=data.get("projectSource"),
            content_hash="",
            raw_content=str(data),
        )
        instance.content_hash = instance.compute_self_hash()
        return instance


class AnnouncementCreate(BaseModel):
    """创建公告的输入模型"""
    title: str = Field(..., min_length=1, max_length=500)
    announcement_type: int = Field(default=1)
    category: str = Field(...)
    publish_date: datetime = Field(...)
    deadline: datetime | None = Field(None)
    url: HttpUrl = Field(...)
    org_name: str | None = Field(None)
    contact_info: str | None = Field(None)
    raw_content: str | None = Field(None)


class AnnouncementUpdate(BaseModel):
    """更新公告的输入模型"""
    title: str | None = Field(None)
    category: str | None = Field(None)
    deadline: datetime | None = Field(None)
    contact_info: str | None = Field(None)
