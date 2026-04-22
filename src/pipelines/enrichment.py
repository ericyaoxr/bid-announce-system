"""
数据增强管道
"""

from typing import TypedDict

from ..models.announcement import Announcement
from ..utils.logger import get_logger

logger = get_logger(__name__)


class EnrichmentResult(TypedDict):
    """增强结果"""

    enriched: bool
    org_name: str | None
    contact_info: str | None
    region: str | None
    estimated_amount: float | None
    errors: list[str]


class EnrichmentPipeline:
    """数据增强管道"""

    def __init__(self) -> None:
        self._steps: list[tuple[str, callable]] = [
            ("extract_org", self._extract_org_step),
            ("extract_contact", self._extract_contact_step),
            ("extract_amount", self._extract_amount_step),
        ]

    async def execute(self, announcement: Announcement) -> EnrichmentResult:
        """
        执行增强管道

        Args:
            announcement: 待增强的公告对象

        Returns:
            EnrichmentResult: 增强结果
        """
        result = EnrichmentResult(
            enriched=False,
            org_name=announcement.org_name,
            contact_info=announcement.contact_info,
            region=None,
            estimated_amount=None,
            errors=[],
        )

        for step_name, step_func in self._steps:
            try:
                step_result = await step_func(announcement, result)
                if step_result:
                    result.update(step_result)
            except Exception as e:
                logger.warning("enrichment_step_failed", step=step_name, error=str(e))
                result["errors"].append(f"{step_name}: {str(e)}")

        result["enriched"] = len(result["errors"]) == 0
        return result

    async def _extract_org_step(
        self, announcement: Announcement, result: EnrichmentResult
    ) -> EnrichmentResult | None:
        """提取机构名称"""
        if announcement.org_name:
            return None

        content = announcement.raw_content or ""

        # 简单正则匹配
        import re

        # 采购人：xxx
        match = re.search(r"采购人[：:]\s*([^\n，,]+)", content)
        if match:
            return {"org_name": match.group(1).strip()}

        # 招租人：xxx
        match = re.search(r"招租人[：:]\s*([^\n，,]+)", content)
        if match:
            return {"org_name": match.group(1).strip()}

        return None

    async def _extract_contact_step(
        self, announcement: Announcement, result: EnrichmentResult
    ) -> EnrichmentResult | None:
        """提取联系方式"""
        if announcement.contact_info:
            return None

        content = announcement.raw_content or ""

        import re

        # 电话
        phone_pattern = r"1[3-9]\d{9}|0\d{2,3}-?\d{7,8}"
        phones = re.findall(phone_pattern, content)
        if phones:
            return {"contact_info": phones[0]}

        # 邮箱
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        emails = re.findall(email_pattern, content)
        if emails:
            return {"contact_info": emails[0]}

        return None

    async def _extract_amount_step(
        self, announcement: Announcement, result: EnrichmentResult
    ) -> EnrichmentResult | None:
        """提取预算金额"""
        content = announcement.raw_content or ""

        import re

        # 预算金额：xxx元
        patterns = [
            r"预算[金额]?[：:]\s*([\d,]+(?:\.\d{2})?)\s*元",
            r"采购预算[：:]\s*([\d,]+(?:\.\d{2})?)\s*元",
            r"最高限价[：:]\s*([\d,]+(?:\.\d{2})?)\s*元",
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                amount_str = match.group(1).replace(",", "")
                try:
                    amount = float(amount_str)
                    return {"estimated_amount": amount}
                except ValueError:
                    continue

        return None
