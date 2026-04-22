"""
数据验证器
"""

import re
from datetime import datetime
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


def validate_phone_number(phone: str | None) -> str | None:
    """验证手机号码格式"""
    if not phone:
        return None

    # 中国手机号正则
    pattern = r"^1[3-9]\d{9}$"
    if re.match(pattern, phone):
        return phone

    # 固定电话正则
    pattern = r"^0\d{2,3}-?\d{7,8}$"
    if re.match(pattern, phone):
        return phone

    logger.warning("invalid_phone_format", phone=phone)
    return None


def validate_email(email: str | None) -> str | None:
    """验证邮箱格式"""
    if not email:
        return None

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if re.match(pattern, email):
        return email

    logger.warning("invalid_email_format", email=email)
    return None


def validate_id_card(id_card: str | None) -> str | None:
    """验证身份证号码格式"""
    if not id_card:
        return None

    # 18位身份证正则
    pattern = r"^[1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$"
    if re.match(pattern, id_card):
        return id_card.upper()

    logger.warning("invalid_id_card_format", id_card=id_card)
    return None


def validate_url(url: str | None) -> str | None:
    """验证URL格式"""
    if not url:
        return None

    pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    if re.match(pattern, url, re.IGNORECASE):
        return url

    logger.warning("invalid_url_format", url=url)
    return None


def sanitize_text(text: str | None, max_length: int = 1000) -> str:
    """清理文本内容"""
    if not text:
        return ""

    # 去除多余空白
    text = re.sub(r"\s+", " ", text)
    # 去除特殊字符
    text = text.strip()

    if len(text) > max_length:
        text = text[:max_length] + "..."

    return text


def validate_date_range(start_date: datetime, end_date: datetime) -> bool:
    """验证日期范围"""
    if start_date > end_date:
        logger.warning("invalid_date_range", start=start_date, end=end_date)
        return False
    return True


class ValidationResult:
    """验证结果封装"""

    def __init__(self, success: bool, data: Any = None, errors: list[str] | None = None) -> None:
        self.success = success
        self.data = data
        self.errors = errors or []

    @classmethod
    def ok(cls, data: Any) -> "ValidationResult":
        """验证成功"""
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, errors: list[str]) -> "ValidationResult":
        """验证失败"""
        return cls(success=False, errors=errors)

    def __bool__(self) -> bool:
        return self.success
