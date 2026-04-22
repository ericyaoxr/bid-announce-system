"""
解析器 - 适配采购平台API
"""

from dataclasses import dataclass, field
from typing import Any

import orjson
from parsel import Selector

from src.models.announcement import Announcement


@dataclass
class ParseResult:
    """解析结果"""

    success: bool
    items: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    total: int | None = None
    page: int | None = None
    page_size: int | None = None
    total_pages: int | None = None
    raw_response: str | None = None


class ListPageParser:
    """
    列表页解析器 - 适配采购平台API

    API响应格式:
    {
        "code": 200,
        "msg": "操作成功",
        "data": {
            "records": [...],
            "total": 28715,
            "size": 20,
            "current": 1,
            "pages": 1436
        }
    }
    """

    def __init__(self, selectors: dict[str, str] | None = None) -> None:
        self._selectors = selectors or {}

    def parse(self, content: bytes | str) -> ParseResult:
        """
        解析API响应内容

        Args:
            content: API响应的JSON内容

        Returns:
            ParseResult: 包含解析结果的对象
        """
        try:
            if isinstance(content, str):
                content = content.encode("utf-8")

            data = orjson.loads(content)

            # 检查响应状态
            code = data.get("code")
            if code != 200:
                return ParseResult(
                    success=False, errors=[f"API返回错误码: {code}, 消息: {data.get('msg')}"]
                )

            # 提取数据部分
            result_data = data.get("data", {})

            # 提取分页信息
            total = result_data.get("total")
            size = result_data.get("size")
            current = result_data.get("current")
            pages = result_data.get("pages")

            # 提取记录列表
            records = result_data.get("records", [])

            return ParseResult(
                success=True,
                items=records,
                total=total,
                page=current,
                page_size=size,
                total_pages=pages,
                raw_response=str(data)[:1000],  # 保留原始响应用于调试
            )

        except orjson.JSONDecodeError as e:
            return ParseResult(success=False, errors=[f"JSON解析失败: {str(e)}"])
        except Exception as e:
            return ParseResult(success=False, errors=[f"解析异常: {str(e)}"])

    def parse_to_announcements(
        self, content: bytes | str, base_url: str = "https://zcpt.szcg.cn"
    ) -> tuple[list[Announcement], list[str]]:
        """
        解析并转换为Announcement对象

        Args:
            content: API响应内容
            base_url: 基础URL

        Returns:
            (成功转换的公告列表, 错误列表)
        """
        result = self.parse(content)
        announcements = []
        errors = []

        if not result.success:
            return [], result.errors

        for i, item in enumerate(result.items):
            try:
                announcement = Announcement.from_api_response(item, base_url)
                announcements.append(announcement)
            except Exception as e:
                errors.append(f"第{i + 1}条记录转换失败: {str(e)}")

        return announcements, errors


class JSONParser:
    """通用JSON解析器"""

    def __init__(self, selectors: dict[str, str] | None = None) -> None:
        self._selectors = selectors or {}

    def parse(self, content: bytes | str) -> ParseResult:
        """解析JSON内容"""
        try:
            if isinstance(content, str):
                content = content.encode("utf-8")

            data = orjson.loads(content)

            # 通用解析：尝试提取列表数据
            items = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                # 尝试常见的数据路径
                for key in ["data", "records", "list", "items", "result"]:
                    if key in data:
                        value = data[key]
                        if isinstance(value, list):
                            items = value
                            break

            return ParseResult(
                success=True,
                items=items,
                total=len(items),
            )

        except orjson.JSONDecodeError as e:
            return ParseResult(success=False, errors=[f"JSON解析失败: {str(e)}"])


class DetailPageParser:
    """详情页解析器 - 用于解析公告详情页面HTML"""

    def __init__(self, selectors: dict[str, str]) -> None:
        self._selectors = selectors

    def parse(self, content: str) -> ParseResult:
        """解析HTML详情页"""
        try:
            sel = Selector(text=content)
            items = []

            # 提取标题
            title = sel.css(self._selectors.get("title", "h1::text")).get()

            # 提取内容
            content_text = sel.css(self._selectors.get("content", "div.content::text")).get()

            # 提取发布时间
            publish_date = sel.css(self._selectors.get("publish_date", "span.time::text")).get()

            if title:
                items.append(
                    {
                        "title": title.strip(),
                        "content": content_text.strip() if content_text else "",
                        "publish_date": publish_date.strip() if publish_date else None,
                    }
                )

            return ParseResult(success=True, items=items)

        except Exception as e:
            return ParseResult(success=False, errors=[f"HTML解析失败: {str(e)}"])
