import json
import smtplib
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any

from src.utils.logger import get_logger

logger = get_logger(__name__)


class WebhookNotifier:
    """通用 Webhook 通知"""

    def __init__(self, url: str, method: str = "POST", headers: dict | None = None):
        self.url = url
        self.method = method
        self.headers = headers or {"Content-Type": "application/json"}

    async def send(self, title: str, content: str, **kwargs: Any) -> bool:
        payload = {
            "title": title,
            "content": content,
            **kwargs,
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.request(
                    self.method, self.url, headers=self.headers, json=payload
                )
                resp.raise_for_status()
                logger.info("Webhook 通知发送成功: %s", title)
                return True
        except Exception as e:
            logger.error("Webhook 通知发送失败: %s", e)
            return False


class FeishuNotifier:
    """飞书机器人通知"""

    def __init__(self, webhook_url: str, secret: str | None = None):
        self.webhook_url = webhook_url
        self.secret = secret

    async def send(self, title: str, content: str, **kwargs: Any) -> bool:
        msg = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": title},
                    "template": "blue",
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": content},
                    }
                ],
            },
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(self.webhook_url, json=msg)
                resp.raise_for_status()
                result = resp.json()
                if result.get("StatusCode") == 0 or result.get("code") == 0:
                    logger.info("飞书通知发送成功: %s", title)
                    return True
                logger.error("飞书通知发送失败: %s", result)
                return False
        except Exception as e:
            logger.error("飞书通知发送失败: %s", e)
            return False


class DingTalkNotifier:
    """钉钉机器人通知"""

    def __init__(self, webhook_url: str, secret: str | None = None):
        self.webhook_url = webhook_url
        self.secret = secret

    async def send(self, title: str, content: str, **kwargs: Any) -> bool:
        msg = {
            "msgtype": "markdown",
            "markdown": {"title": title, "text": content},
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(self.webhook_url, json=msg)
                resp.raise_for_status()
                result = resp.json()
                if result.get("errcode") == 0:
                    logger.info("钉钉通知发送成功: %s", title)
                    return True
                logger.error("钉钉通知发送失败: %s", result)
                return False
        except Exception as e:
            logger.error("钉钉通知发送失败: %s", e)
            return False


class WeComNotifier:
    """企业微信机器人通知"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send(self, title: str, content: str, **kwargs: Any) -> bool:
        msg = {
            "msgtype": "markdown",
            "markdown": {"content": f"## {title}\n{content}"},
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(self.webhook_url, json=msg)
                resp.raise_for_status()
                result = resp.json()
                if result.get("errcode") == 0:
                    logger.info("企业微信通知发送成功: %s", title)
                    return True
                logger.error("企业微信通知发送失败: %s", result)
                return False
        except Exception as e:
            logger.error("企业微信通知发送失败: %s", e)
            return False


class EmailNotifier:
    """邮件通知"""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int = 465,
        username: str = "",
        password: str = "",
        use_ssl: bool = True,
        sender: str = "",
        recipients: list[str] | None = None,
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.sender = sender or username
        self.recipients = recipients or []

    def send(self, title: str, content: str, **kwargs: Any) -> bool:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = title
        msg["From"] = self.sender
        msg["To"] = ", ".join(self.recipients)
        msg.attach(MIMEText(content, "html", "utf-8"))

        try:
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            server.login(self.username, self.password)
            server.sendmail(self.sender, self.recipients, msg.as_string())
            server.quit()
            logger.info("邮件通知发送成功: %s", title)
            return True
        except Exception as e:
            logger.error("邮件通知发送失败: %s", e)
            return False


class NotificationService:
    """统一通知服务"""

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.notifiers: list[Any] = []
        self._init_notifiers()

    def _init_notifiers(self) -> None:
        for notifier_cfg in self.config.get("notifiers", []):
            ntype = notifier_cfg.get("type")
            enabled = notifier_cfg.get("enabled", True)
            if not enabled:
                continue

            if ntype == "webhook":
                self.notifiers.append(
                    WebhookNotifier(
                        url=notifier_cfg["url"],
                        method=notifier_cfg.get("method", "POST"),
                        headers=notifier_cfg.get("headers"),
                    )
                )
            elif ntype == "feishu":
                self.notifiers.append(
                    FeishuNotifier(
                        webhook_url=notifier_cfg["webhook_url"],
                        secret=notifier_cfg.get("secret"),
                    )
                )
            elif ntype == "dingtalk":
                self.notifiers.append(
                    DingTalkNotifier(
                        webhook_url=notifier_cfg["webhook_url"],
                        secret=notifier_cfg.get("secret"),
                    )
                )
            elif ntype == "wecom":
                self.notifiers.append(
                    WeComNotifier(webhook_url=notifier_cfg["webhook_url"])
                )
            elif ntype == "email":
                self.notifiers.append(
                    EmailNotifier(
                        smtp_host=notifier_cfg["smtp_host"],
                        smtp_port=notifier_cfg.get("smtp_port", 465),
                        username=notifier_cfg["username"],
                        password=notifier_cfg["password"],
                        use_ssl=notifier_cfg.get("use_ssl", True),
                        sender=notifier_cfg.get("sender"),
                        recipients=notifier_cfg.get("recipients", []),
                    )
                )

    async def send(self, title: str, content: str, **kwargs: Any) -> dict[str, bool]:
        results = {}
        for i, notifier in enumerate(self.notifiers):
            ntype = type(notifier).__name__
            try:
                if isinstance(notifier, EmailNotifier):
                    ok = notifier.send(title, content, **kwargs)
                else:
                    ok = await notifier.send(title, content, **kwargs)
                results[ntype] = ok
            except Exception as e:
                logger.error("通知发送异常 [%s]: %s", ntype, e)
                results[ntype] = False
        return results
