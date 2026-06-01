from app.integrations.ai.base import AIProvider, AIResponse


class LocalAIProvider(AIProvider):
    provider_name = "local"
    model = "deterministic-fallback"

    async def summarize(self, text: str) -> AIResponse:
        words = text.split()
        output = " ".join(words[:40])
        if len(words) > 40:
            output += "..."
        return AIResponse(self.provider_name, self.model, output, self._usage(text, output))

    async def classify(self, text: str, labels: list[str]) -> AIResponse:
        normalized = text.lower()
        selected = next((label for label in labels if label.lower() in normalized), labels[0])
        return AIResponse(self.provider_name, self.model, selected, self._usage(text, selected))

    def _usage(self, prompt: str, completion: str) -> dict[str, int]:
        prompt_tokens = max(1, len(prompt.split()))
        completion_tokens = max(1, len(completion.split()))
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        }

