from typing import Any, Protocol

from src.config.settings import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AnalysisResult:
    def __init__(
        self,
        summary: str = "",
        tags: list[str] | None = None,
        risk_level: str = "low",
        anomalies: list[str] | None = None,
        raw_response: dict[str, Any] | None = None,
    ) -> None:
        self.summary = summary
        self.tags = tags or []
        self.risk_level = risk_level
        self.anomalies = anomalies or []
        self.raw_response = raw_response


class AIAnalyzer(Protocol):
    async def analyze(self, announcement: dict[str, Any]) -> AnalysisResult: ...


class DeepSeekAnalyzer:
    def __init__(self, api_key: str, base_url: str = "", model: str = "deepseek-chat") -> None:
        self.api_key = api_key
        self.base_url = base_url or "https://api.deepseek.com"
        self.model = model

    async def analyze(self, announcement: dict[str, Any]) -> AnalysisResult:
        import httpx

        prompt = self._build_prompt(announcement)
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3,
                        "max_tokens": 500,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    return self._parse_response(content, announcement)
                else:
                    logger.warning("ai_analyze_failed", status=resp.status_code)
                    return AnalysisResult()
        except Exception as e:
            logger.error("ai_analyze_error", error=str(e))
            return AnalysisResult()

    def _build_prompt(self, announcement: dict[str, Any]) -> str:
        title = announcement.get("title", "")
        amount = announcement.get("winner_amount", "")
        supplier = announcement.get("winner_supplier", "")
        tenderer = announcement.get("tenderer_name", "")
        category = announcement.get("category", "")

        return (
            f"请分析以下中标结果，给出摘要、标签和风险评估：\n"
            f"标题: {title}\n"
            f"分类: {category}\n"
            f"招标人: {tenderer}\n"
            f"中标人: {supplier}\n"
            f"中标金额: {amount}\n\n"
            f'请以JSON格式返回: {{"summary": "...", "tags": [...], '
            f'"risk_level": "low|medium|high", "anomalies": [...]}}'
        )

    def _parse_response(self, content: str, announcement: dict[str, Any]) -> AnalysisResult:
        import json

        try:
            data = json.loads(content)
            return AnalysisResult(
                summary=data.get("summary", ""),
                tags=data.get("tags", []),
                risk_level=data.get("risk_level", "low"),
                anomalies=data.get("anomalies", []),
                raw_response=data,
            )
        except (json.JSONDecodeError, TypeError):
            return AnalysisResult(summary=content[:200])


class OllamaAnalyzer:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5:7b") -> None:
        self.base_url = base_url
        self.model = model

    async def analyze(self, announcement: dict[str, Any]) -> AnalysisResult:
        import httpx

        prompt = DeepSeekAnalyzer("", "")._build_prompt(announcement)
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content = data.get("response", "")
                    return DeepSeekAnalyzer("", "")._parse_response(content, announcement)
                return AnalysisResult()
        except Exception as e:
            logger.error("ollama_analyze_error", error=str(e))
            return AnalysisResult()


class NoOpAnalyzer:
    async def analyze(self, announcement: dict[str, Any]) -> AnalysisResult:
        return AnalysisResult()


def create_analyzer() -> AIAnalyzer:
    settings = get_settings()
    provider = settings.ai_provider.lower() if settings.ai_provider else ""

    if provider == "deepseek" and settings.ai_api_key:
        return DeepSeekAnalyzer(
            api_key=settings.ai_api_key,
            base_url=settings.ai_base_url,
            model=settings.ai_model or "deepseek-chat",
        )
    elif provider == "ollama":
        return OllamaAnalyzer(
            base_url=settings.ai_base_url or "http://localhost:11434",
            model=settings.ai_model or "qwen2.5:7b",
        )
    elif provider == "openai" and settings.ai_api_key:
        return DeepSeekAnalyzer(
            api_key=settings.ai_api_key,
            base_url=settings.ai_base_url or "https://api.openai.com",
            model=settings.ai_model or "gpt-4o-mini",
        )
    else:
        return NoOpAnalyzer()
