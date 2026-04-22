"""爬虫基类 - 所有网站爬虫的抽象基类"""

from __future__ import annotations

import abc
from typing import Any


class BaseCrawler(abc.ABC):
    """所有网站爬虫必须继承此类"""

    @abc.abstractmethod
    async def crawl_list(self, **kwargs) -> int:
        """抓取列表页，返回新增记录数"""

    @abc.abstractmethod
    async def crawl_details(self, **kwargs) -> int:
        """抓取详情页，返回成功数"""

    @abc.abstractmethod
    async def close(self) -> None:
        """关闭爬虫连接"""

    def get_site_info(self) -> dict[str, Any]:
        """返回站点信息"""
        return {
            "site_id": getattr(self, "site_id", ""),
            "site_name": getattr(self, "site_name", ""),
            "base_url": getattr(self, "base_url", ""),
        }
