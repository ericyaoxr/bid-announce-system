"""爬虫注册中心 - 支持多网站采集"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.crawlers.base import BaseCrawler

_registry: dict[str, dict] = {}


def register_crawler(
    crawler_cls: type,
    *,
    site_id: str,
    site_name: str,
    base_url: str,
    description: str = "",
    enabled: bool = True,
) -> None:
    _registry[site_id] = {
        "cls": crawler_cls,
        "site_id": site_id,
        "site_name": site_name,
        "base_url": base_url,
        "description": description,
        "enabled": enabled,
    }


def get_crawler(site_id: str, **kwargs) -> BaseCrawler:
    entry = _registry.get(site_id)
    if not entry:
        raise ValueError(f"Unknown crawler site_id: {site_id}")
    if not entry["enabled"]:
        raise ValueError(f"Crawler disabled: {site_id}")
    return entry["cls"](**kwargs)


def list_crawlers() -> list[dict]:
    return [
        {
            "site_id": v["site_id"],
            "site_name": v["site_name"],
            "base_url": v["base_url"],
            "description": v["description"],
            "enabled": v["enabled"],
        }
        for v in _registry.values()
    ]
