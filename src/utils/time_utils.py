"""
时间工具函数
"""
from datetime import UTC, datetime, timedelta, timezone
from typing import TypeVar

import structlog
from dateutil import parser as date_parser

logger = structlog.get_logger(__name__)

T = TypeVar("T")


def now_utc() -> datetime:
    """获取当前UTC时间"""
    return datetime.now(UTC)


def now_china() -> datetime:
    """获取当前中国时区时间"""
    return datetime.now(timezone(timedelta(hours=8)))


def parse_datetime(date_string: str | None) -> datetime | None:
    """
    解析日期字符串为datetime对象

    Args:
        date_string: ISO格式或常见格式的日期字符串

    Returns:
        datetime对象，解析失败返回None
    """
    if not date_string:
        return None

    try:
        return date_parser.parse(date_string)
    except (ValueError, TypeError) as e:
        logger.warning("date_parse_failed", date_string=date_string, error=str(e))
        return None


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化datetime为字符串"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.strftime(fmt)


def is_within_days(dt: datetime, days: int) -> bool:
    """检查datetime是否在指定天数内"""
    cutoff = now_utc() - timedelta(days=days)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt >= cutoff


def get_date_range(days: int = 365) -> tuple[datetime, datetime]:
    """获取日期范围（从过去某天到现在）"""
    end_date = now_utc()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date
