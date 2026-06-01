from app.integrations.ai.local import LocalAIProvider
from app.schemas.ai import AIResult


class AIService:
    def __init__(self):
        self.providers = {"local": LocalAIProvider()}

    async def summarize(self, text: str, provider: str = "local") -> AIResult:
        adapter = self.providers.get(provider, self.providers["local"])
        result = await adapter.summarize(text)
        return AIResult(provider=result.provider, model=result.model, output=result.output, usage=result.usage)

    async def classify(self, text: str, labels: list[str], provider: str = "local") -> AIResult:
        adapter = self.providers.get(provider, self.providers["local"])
        result = await adapter.classify(text, labels)
        return AIResult(provider=result.provider, model=result.model, output=result.output, usage=result.usage)

