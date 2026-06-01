import asyncio
import json
import logging
import time
from typing import Any, AsyncGenerator

import httpx

from app.integrations.ai.base import AIProvider, AIResponse, estimate_tokens

logger = logging.getLogger(__name__)


class OllamaAIProvider(AIProvider):
    """
    Production-grade AI adapter integration for local LLM inference engines using Ollama's REST API.
    """

    def __init__(self, base_url: str = "http://localhost:11434", default_model: str = "llama3"):
        self.base_url = base_url.rstrip("/")
        self._default_model = default_model

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def default_model(self) -> str:
        return self._default_model

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        timeout: float = 30.0,
        options: dict[str, Any] | None = None,
    ) -> AIResponse:
        model = model or self.default_model
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": options or {},
        }

        max_retries = 3
        backoff_base = 0.5
        last_exception = None

        for attempt in range(max_retries):
            start_time = time.perf_counter()
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, json=payload, timeout=timeout)
                    response.raise_for_status()

                    data = response.json()
                    output = data.get("response", "")

                    latency_ms = int((time.perf_counter() - start_time) * 1000)

                    # Extract actual token counts from Ollama, fall back to estimators if missing
                    prompt_tokens = data.get("prompt_eval_count")
                    if prompt_tokens is None:
                        prompt_tokens = estimate_tokens(prompt)

                    completion_tokens = data.get("eval_count")
                    if completion_tokens is None:
                        completion_tokens = estimate_tokens(output)

                    usage = {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": prompt_tokens + completion_tokens,
                    }

                    return AIResponse(
                        provider=self.provider_name,
                        model=model,
                        output=output,
                        usage=usage,
                        latency_ms=latency_ms,
                    )
            except Exception as exc:
                last_exception = exc
                latency_ms = int((time.perf_counter() - start_time) * 1000)
                logger.warning(
                    f"Ollama request failed on attempt {attempt + 1}/{max_retries} "
                    f"in {latency_ms}ms: {str(exc)}"
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(backoff_base * (attempt + 1))

        # If retries completely exhaust, raise exception
        raise RuntimeError(f"Ollama AI provider failed after {max_retries} attempts. Last error: {str(last_exception)}")

    async def generate_stream(
        self,
        prompt: str,
        model: str | None = None,
        timeout: float = 30.0,
        options: dict[str, Any] | None = None,
    ) -> AsyncGenerator[str, None]:
        model = model or self.default_model
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": options or {},
        }

        async with httpx.AsyncClient() as client:
            async with client.stream("POST", url, json=payload, timeout=timeout) as response:
                response.raise_for_status()
                async for line in response.iter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            yield data.get("response", "")
                        except Exception:
                            pass

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        timeout: float = 30.0,
        options: dict[str, Any] | None = None,
    ) -> AIResponse:
        model = model or self.default_model
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": options or {},
        }

        max_retries = 3
        backoff_base = 0.5
        last_exception = None

        for attempt in range(max_retries):
            start_time = time.perf_counter()
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, json=payload, timeout=timeout)
                    response.raise_for_status()

                    data = response.json()
                    output_msg = data.get("message", {})
                    output = output_msg.get("content", "")

                    latency_ms = int((time.perf_counter() - start_time) * 1000)

                    # Extract actual token counts from Ollama, fall back to estimators if missing
                    prompt_tokens = data.get("prompt_eval_count")
                    if prompt_tokens is None:
                        prompt_tokens = sum(estimate_tokens(m.get("content", "")) for m in messages)

                    completion_tokens = data.get("eval_count")
                    if completion_tokens is None:
                        completion_tokens = estimate_tokens(output)

                    usage = {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": prompt_tokens + completion_tokens,
                    }

                    return AIResponse(
                        provider=self.provider_name,
                        model=model,
                        output=output,
                        usage=usage,
                        latency_ms=latency_ms,
                    )
            except Exception as exc:
                last_exception = exc
                latency_ms = int((time.perf_counter() - start_time) * 1000)
                logger.warning(
                    f"Ollama chat request failed on attempt {attempt + 1}/{max_retries} "
                    f"in {latency_ms}ms: {str(exc)}"
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(backoff_base * (attempt + 1))

        raise RuntimeError(f"Ollama AI chat provider failed after {max_retries} attempts. Last error: {str(last_exception)}")

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        timeout: float = 30.0,
        options: dict[str, Any] | None = None,
    ) -> AsyncGenerator[str, None]:
        model = model or self.default_model
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": options or {},
        }

        async with httpx.AsyncClient() as client:
            async with client.stream("POST", url, json=payload, timeout=timeout) as response:
                response.raise_for_status()
                async for line in response.iter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            yield data.get("message", {}).get("content", "")
                        except Exception:
                            pass
