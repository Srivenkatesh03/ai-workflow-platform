import asyncio
import time
from typing import Any, AsyncGenerator

from app.integrations.ai.base import AIProvider, AIResponse, estimate_tokens


class MockAIProvider(AIProvider):
    """
    Simulated mock provider for developer sandboxes, unit tests, and robust system fallbacks.
    """

    def __init__(self, model: str = "mock-gpt-4"):
        self._model = model

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def default_model(self) -> str:
        return self._model

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        timeout: float = 30.0,
        options: dict[str, Any] | None = None,
    ) -> AIResponse:
        start_time = time.perf_counter()
        # Simulate network latency
        await asyncio.sleep(0.02)

        prompt_lower = prompt.lower()
        if "classify" in prompt_lower:
            # Deterministic label selector for testing
            output = "animal"
            for lbl in ["finance", "technology", "billing", "hr"]:
                if lbl in prompt_lower:
                    output = lbl
                    break
        elif "summarize" in prompt_lower:
            # Deterministic summarizer output
            output = "The quick brown fox jumps over the lazy dog repeatedly until it gets tired."
        else:
            output = f"Mock completion response for prompt starting with: {prompt[:30]}"

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
        chunks = ["This ", "is ", "a ", "mock ", "streaming ", "completion."]
        for chunk in chunks:
            await asyncio.sleep(0.01)
            yield chunk

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        timeout: float = 30.0,
        options: dict[str, Any] | None = None,
    ) -> AIResponse:
        start_time = time.perf_counter()
        await asyncio.sleep(0.02)

        last_msg = messages[-1]["content"] if messages else ""
        output = f"Mock chat response for message: {last_msg}"

        latency_ms = int((time.perf_counter() - start_time) * 1000)
        prompt_tokens = sum(estimate_tokens(m.get("content", "")) for m in messages)
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

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        timeout: float = 30.0,
        options: dict[str, Any] | None = None,
    ) -> AsyncGenerator[str, None]:
        chunks = ["This ", "is ", "a ", "mock ", "chat ", "streaming ", "completion."]
        for chunk in chunks:
            await asyncio.sleep(0.01)
            yield chunk
