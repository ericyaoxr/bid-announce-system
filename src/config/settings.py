"""
应用配置 - pydantic-settings
"""
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        case_sensitive=False,
    )

    # 模式
    mode: Literal["development", "staging", "production"] = "development"

    # 调试
    debug: bool = False

    # 数据库
    database_url: str = "postgresql://user:password@localhost:5432/scraper_db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # 采集数据配置
    target_base_url: str = "https://zcpt.szcg.cn"
    crawler_rate_limit_rpm: int = 60
    crawler_batch_size: int = 20
    crawler_max_retries: int = 3
    crawler_timeout: float = 30.0

    # 日志
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "text"] = "json"

    # API配置
    api_base_url: str = "https://zcpt.szcg.cn/group-tendering-website"

    # 调度配置
    scheduler_enabled: bool = True
    incremental_crawl_cron: str = "0 2 * * *"  # 每天凌晨2点
    full_crawl_cron: str = "0 3 * * 0"  # 每周日凌晨3点

    # 数据保留
    data_retention_days: int = 365

    # 告警配置
    alert_enabled: bool = False
    alert_webhook_url: str = ""


@lru_cache
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
