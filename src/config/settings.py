from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        case_sensitive=False,
    )

    mode: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    secret_key: str = "change-me-to-a-random-secret-key-in-production"
    allowed_origins: str = "http://localhost:8000,http://localhost:5173"
    access_token_expire_minutes: int = 1440
    algorithm: str = "HS256"

    db_path: str = "data/announcements_deep.db"

    crawler_rate_limit_rpm: int = 120
    crawler_default_pages: int = 10
    crawler_batch_size: int = 20
    crawler_max_retries: int = 3
    crawler_timeout: float = 30.0

    scheduler_enabled: bool = True
    scheduler_incremental_cron: str = "0 2 * * *"
    scheduler_full_cron: str = "0 3 * * 0"

    notification_enabled: bool = False
    notification_webhook_url: str = ""

    ai_provider: str = ""
    ai_api_key: str = ""
    ai_base_url: str = ""
    ai_model: str = ""

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "text"] = "json"

    api_base_url: str = "https://zcpt.szcg.cn/group-tendering-website"

    data_retention_days: int = 365

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
