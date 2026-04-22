from typing import Protocol

from src.utils.logger import get_logger

logger = get_logger(__name__)


class NotificationMessage:
    def __init__(
        self, title: str, body: str, level: str = "info", data: dict | None = None
    ) -> None:
        self.title = title
        self.body = body
        self.level = level
        self.data = data or {}


class NotificationChannel(Protocol):
    async def send(self, message: NotificationMessage) -> bool: ...


class WebhookChannel:
    def __init__(self, url: str) -> None:
        self.url = url

    async def send(self, message: NotificationMessage) -> bool:
        import httpx

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    self.url,
                    json={
                        "title": message.title,
                        "body": message.body,
                        "level": message.level,
                        "data": message.data,
                    },
                )
                if resp.status_code < 400:
                    logger.info("webhook_sent", url=self.url, status=resp.status_code)
                    return True
                else:
                    logger.warning("webhook_failed", url=self.url, status=resp.status_code)
                    return False
        except Exception as e:
            logger.error("webhook_error", url=self.url, error=str(e))
            return False


class FeishuChannel:
    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    async def send(self, message: NotificationMessage) -> bool:
        import httpx

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    self.webhook_url,
                    json={
                        "msg_type": "interactive",
                        "card": {
                            "header": {"title": {"tag": "plain_text", "content": message.title}},
                            "elements": [{"tag": "markdown", "content": message.body}],
                        },
                    },
                )
                return resp.status_code < 400
        except Exception as e:
            logger.error("feishu_error", error=str(e))
            return False


class DingTalkChannel:
    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    async def send(self, message: NotificationMessage) -> bool:
        import httpx

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    self.webhook_url,
                    json={
                        "msgtype": "markdown",
                        "markdown": {"title": message.title, "text": message.body},
                    },
                )
                return resp.status_code < 400
        except Exception as e:
            logger.error("dingtalk_error", error=str(e))
            return False
