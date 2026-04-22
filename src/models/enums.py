"""
枚举类型定义
"""

from enum import StrEnum


class AnnouncementType(StrEnum):
    """公示类型枚举"""

    PROCUREMENT = "采购公告"
    CHANGE = "变更公告"
    CANDIDATE = "候选人公示"
    RESULT = "结果公示"
    INVITATION = "邀请函"
    OTHER = "其他"

    @classmethod
    def from_string(cls, value: str) -> "AnnouncementType":
        """从字符串解析枚举值"""
        value = value.strip()
        for item in cls:
            if item.value == value or item.name == value.upper():
                return item
        return cls.OTHER


class Category(StrEnum):
    """采购类别枚举"""

    ENGINEERING = "工程"
    GOODS = "货物"
    SERVICE = "服务"
    OTHER = "其他"

    @classmethod
    def from_string(cls, value: str) -> "Category":
        """从字符串解析枚举值"""
        value = value.strip()
        for item in cls:
            if item.value == value or item.name == value.upper():
                return item
        return cls.OTHER


class CrawlerStatus(StrEnum):
    """采集数据运行状态"""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class DataSource(StrEnum):
    """数据来源"""

    OFFICIAL = "zcpt.szcg.cn"
    STAGING = "staging.zcpt.szcg.cn"
