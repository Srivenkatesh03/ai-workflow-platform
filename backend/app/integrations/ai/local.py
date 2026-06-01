import asyncio
import time
from typing import Any, AsyncGenerator

from app.integrations.ai.base import AIProvider, AIResponse, estimate_tokens


class LocalAIProvider(AIProvider):
    """
    Legacy local deterministic provider maintained for backward compatibility.
    """

    @property
    def provider_name(self) -> str:
        return "local"

    @property
    def default_model(self) -> str:
        return "deterministic-fallback"

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        timeout: float = 30.0,
        options: dict[str, Any] | None = None,
    ) -> AIResponse:
        start_time = time.perf_counter()
        await asyncio.sleep(0.01)

        words = prompt.split()
        output = " ".join(words[:40])
        if len(words) > 40:
            output += "..."

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        prompt_tokens = estimate_tokens(prompt)
        completion_tokens = estimate_tokens(output)
        usage = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        }

        return AIResponse(
            provider=self.provider_name,
            model=model or self.default_model,
            output=output,
            usage=usage,
            latency_ms=latency_ms,
        )

    async def generate_stream(
        self,
        prompt: str,
        model: str | None = None,
        timeout: float = 30.0,
        options: dict[str, Any] | None = None,
    ) -> AsyncGenerator[str, None]:
        words = prompt.split()[:40]
        for word in words:
            await asyncio.sleep(0.005)
            yield word + " "

    async def summarize(self, text: str, model: str | None = None, timeout: float = 30.0) -> AIResponse:
        """
        Legacy deterministic summarizer behavior: returns first 40 words.
        """
        start_time = time.perf_counter()
        await asyncio.sleep(0.01)

        words = text.split()
        output = " ".join(words[:40])
        if len(words) > 40:
            output += "..."

        latency_ms = int((time.perf_counter() - start_time) * 1000)
        prompt_tokens = estimate_tokens(text)
        completion_tokens = estimate_tokens(output)

        return AIResponse(
            provider=self.provider_name,
            model=model or self.default_model,
            output=output,
            usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
            latency_ms=latency_ms,
        )

    async def classify(self, text: str, labels: list[str], model: str | None = None, timeout: float = 30.0) -> AIResponse:
        """
        Legacy deterministic classifier behavior: searches category words in lowercase text.
        """
        start_time = time.perf_counter()
        await asyncio.sleep(0.01)

        normalized = text.lower()
        selected = next((label for label in labels if label.lower() in normalized), labels[0])

        latency_ms = int((time.perf_counter() - start_time) * 1000)
        prompt_tokens = estimate_tokens(text)
        completion_tokens = estimate_tokens(selected)

        return AIResponse(
            provider=self.provider_name,
            model=model or self.default_model,
            output=selected,
            usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
            latency_ms=latency_ms,
        )

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        timeout: float = 30.0,
        options: dict[str, Any] | None = None,
    ) -> AIResponse:
        start_time = time.perf_counter()
        await asyncio.sleep(0.01)

        last_msg = messages[-1]["content"] if messages else ""
        words = last_msg.split()
        output = " ".join(words[:40])
        if len(words) > 40:
            output += "..."

        latency_ms = int((time.perf_counter() - start_time) * 1000)
        prompt_tokens = sum(estimate_tokens(m.get("content", "")) for m in messages)
        completion_tokens = estimate_tokens(output)

        return AIResponse(
            provider=self.provider_name,
            model=model or self.default_model,
            output=output,
            usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
            latency_ms=latency_ms,
        )

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        timeout: float = 30.0,
        options: dict[str, Any] | None = None,
    ) -> AsyncGenerator[str, None]:
        last_msg = messages[-1]["content"] if messages else ""
        words = last_msg.split()[:40]
        for word in words:
            await asyncio.sleep(0.005)
            yield word + " "
