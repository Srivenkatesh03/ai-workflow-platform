from dataclasses import dataclass


@dataclass(frozen=True)
class AIResponse:
    provider: str
    model: str
    output: str
    usage: dict[str, int]


class AIProvider:
    provider_name = "base"
    model = "unknown"

    async def summarize(self, text: str) -> AIResponse:
        raise NotImplementedError

    async def classify(self, text: str, labels: list[str]) -> AIResponse:
        raise NotImplementedError

