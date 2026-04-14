"""
数据清洗管道
"""
import re
from typing import TypedDict

from ..models.announcement import Announcement
from ..utils.logger import get_logger

logger = get_logger(__name__)


class CleaningResult(TypedDict):
    """清洗结果"""
    cleaned: bool
    title: str
    content: str | None
    errors: list[str]


class CleaningPipeline:
    """数据清洗管道"""

    def __init__(self) -> None:
        self._rules: list[tuple[str, callable]] = [
            ("normalize_whitespace", self._normalize_whitespace),
            ("remove_html_tags", self._remove_html_tags),
            ("normalize_punctuation", self._normalize_punctuation),
            ("trim_content", self._trim_content),
        ]

    async def execute(self, announcement: Announcement) -> CleaningResult:
        """
        执行清洗管道

        Args:
            announcement: 待清洗的公告对象

        Returns:
            CleaningResult: 清洗结果
        """
        title = announcement.title
        content = announcement.raw_content or ""
        errors = []

        for rule_name, rule_func in self._rules:
            try:
                title, content = rule_func(title, content)
            except Exception as e:
                logger.warning("cleaning_rule_failed", rule=rule_name, error=str(e))
                errors.append(f"{rule_name}: {str(e)}")

        # 更新对象
        announcement.title = title
        announcement.raw_content = content

        return CleaningResult(
            cleaned=len(errors) == 0,
            title=title,
            content=content,
            errors=errors,
        )

    def _normalize_whitespace(self, title: str, content: str) -> tuple[str, str]:
        """规范化空白字符"""
        # 将多个空格合并为一个
        title = re.sub(r"\s+", " ", title).strip()
        content = re.sub(r"\s+", " ", content)
        return title, content

    def _remove_html_tags(self, title: str, content: str) -> tuple[str, str]:
        """移除HTML标签"""
        # 移除HTML标签
        clean = re.compile("<.*?>")
        title = re.sub(clean, "", title)
        content = re.sub(clean, "", content)

        # 解码HTML实体
        html_entities = {
            "&nbsp;": " ",
            "&amp;": "&",
            "&lt;": "<",
            "&gt;": ">",
            "&quot;": '"',
            "&#39;": "'",
        }
        for entity, char in html_entities.items():
            content = content.replace(entity, char)

        return title, content

    def _normalize_punctuation(self, title: str, content: str) -> tuple[str, str]:
        """规范化标点符号"""
        # 将中文标点转换为英文（可选）
        punct_map = {
            "，": ",",
            "。": ".",
            "：": ":",
            "；": ";",
            "！": "!",
            "？": "?",
            "（": "(",
            "）": ")",
            "【": "[",
            "】": "]",
        }

        for cn, en in punct_map.items():
            content = content.replace(cn, en)

        return title, content

    def _trim_content(self, title: str, content: str) -> tuple[str, str]:
        """裁剪内容"""
        # 移除首尾空白
        title = title.strip()
        content = content.strip()

        # 限制标题长度
        if len(title) > 500:
            title = title[:497] + "..."

        # 限制内容长度（可选，避免过大）
        max_content_length = 100000  # 100KB
        if len(content) > max_content_length:
            content = content[:max_content_length] + "...[内容已截断]"

        return title, content
