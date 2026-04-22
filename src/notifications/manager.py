from src.config.settings import get_settings
from src.notifications.channels import (
    DingTalkChannel,
    FeishuChannel,
    NotificationChannel,
    NotificationMessage,
    WebhookChannel,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class NotificationManager:
    def __init__(self) -> None:
        self._channels: list[NotificationChannel] = []
        self._setup_channels()

    def _setup_channels(self) -> None:
        settings = get_settings()
        if not settings.notification_enabled:
            return
        if settings.notification_webhook_url:
            url = settings.notification_webhook_url
            if "feishu" in url or "lark" in url:
                self._channels.append(FeishuChannel(url))
            elif "dingtalk" in url or "oapi.dingtalk" in url:
                self._channels.append(DingTalkChannel(url))
            else:
                self._channels.append(WebhookChannel(url))

    async def notify(
        self, title: str, body: str, level: str = "info", data: dict | None = None
    ) -> None:
        if not self._channels:
            return
        message = NotificationMessage(title=title, body=body, level=level, data=data)
        for channel in self._channels:
            try:
                await channel.send(message)
            except Exception as e:
                logger.error(
                    "notification_send_failed", channel=type(channel).__name__, error=str(e)
                )

    async def notify_crawl_complete(
        self, mode: str, total: int, with_winner: int, elapsed: float
    ) -> None:
        await self.notify(
            title="采集任务完成",
            body=f"模式: {mode}\n总记录: {total}\n有中标: {with_winner}\n耗时: {elapsed:.1f}s",
            level="info",
            data={"mode": mode, "total": total, "with_winner": with_winner, "elapsed": elapsed},
        )

    async def notify_crawl_error(self, mode: str, error: str) -> None:
        await self.notify(
            title="采集任务失败",
            body=f"模式: {mode}\n错误: {error}",
            level="error",
            data={"mode": mode, "error": error},
        )


_notification_manager: NotificationManager | None = None


def get_notification_manager() -> NotificationManager:
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager
