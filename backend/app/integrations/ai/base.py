import abc
import logging
from dataclasses import dataclass
from typing import Any, AsyncGenerator

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AIResponse:
    provider: str
    model: str
    output: str
    usage: dict[str, int]  # prompt_tokens, completion_tokens, total_tokens
    latency_ms: int = 0


def estimate_tokens(text: str) -> int:
    """
    Estimates the number of tokens in a given text locally and deterministically.
    Approximates ~4 characters per token for English text.
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


class PromptTemplate:
    """
    Represents a prompt template that can format static/dynamic variables.
    """

    def __init__(self, template: str):
        self.template = template

    def render(self, **kwargs: Any) -> str:
        return self.template.format(**kwargs)


class AIProvider(abc.ABC):
    """
    Core abstract class defining standard local and cloud AI provider interactions.
    """

    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def default_model(self) -> str:
        pass

    @abc.abstractmethod
    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        timeout: float = 30.0,
        options: dict[str, Any] | None = None,
    ) -> AIResponse:
        """
        Asynchronously generates a complete response for a prompt.
        """
        pass

    @abc.abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        model: str | None = None,
        timeout: float = 30.0,
        options: dict[str, Any] | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Asynchronously streams token chunks for a prompt.
        """
        pass
        yield ""  # Keep it a generator

    @abc.abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        timeout: float = 30.0,
        options: dict[str, Any] | None = None,
    ) -> AIResponse:
        """
        Asynchronously generates a complete response for a chat conversation.
        """
        pass

    @abc.abstractmethod
    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        timeout: float = 30.0,
        options: dict[str, Any] | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Asynchronously streams token chunks for a chat conversation.
        """
        pass
        yield ""

    async def summarize(self, text: str, model: str | None = None, timeout: float = 30.0) -> AIResponse:
        """
        Summarizes text using the provider's general generation.
        """
        prompt = f"Summarize the following text concisely. Keep it under 40 words:\n\n{text}"
        return await self.generate(prompt, model=model, timeout=timeout)

    async def classify(self, text: str, labels: list[str], model: str | None = None, timeout: float = 30.0) -> AIResponse:
        """
        Classifies text using the provider's general generation.
        """
        labels_str = ", ".join(labels)
        prompt = (
            f"Classify the following text into exactly one of these categories: [{labels_str}].\n"
            f"Respond with ONLY the exact matching category name and absolutely nothing else.\n\n"
            f"Text: {text}"
        )
        return await self.generate(prompt, model=model, timeout=timeout)


class FallbackAIProvider(AIProvider):
    """
    Wraps two AI providers to support automatic, transparent fallback chain.
    """

    def __init__(self, primary: AIProvider, fallback: AIProvider):
        self.primary = primary
        self.fallback = fallback

    @property
    def provider_name(self) -> str:
        return f"{self.primary.provider_name}_with_fallback"

    @property
    def default_model(self) -> str:
        return self.primary.default_model

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        timeout: float = 30.0,
        options: dict[str, Any] | None = None,
    ) -> AIResponse:
        try:
            return await self.primary.generate(prompt, model=model, timeout=timeout, options=options)
        except Exception as exc:
            logger.warning(
                f"Primary AI provider '{self.primary.provider_name}' failed: {str(exc)}. "
                f"Falling back to '{self.fallback.provider_name}'..."
            )
            return await self.fallback.generate(prompt, model=model, timeout=timeout, options=options)

    async def generate_stream(
        self,
        prompt: str,
        model: str | None = None,
        timeout: float = 30.0,
        options: dict[str, Any] | None = None,
    ) -> AsyncGenerator[str, None]:
        try:
            async for chunk in self.primary.generate_stream(prompt, model=model, timeout=timeout, options=options):
                yield chunk
        except Exception as exc:
            logger.warning(
                f"Primary AI streaming provider '{self.primary.provider_name}' failed: {str(exc)}. "
                f"Falling back to '{self.fallback.provider_name}'..."
            )
            async for chunk in self.fallback.generate_stream(prompt, model=model, timeout=timeout, options=options):
                yield chunk

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        timeout: float = 30.0,
        options: dict[str, Any] | None = None,
    ) -> AIResponse:
        try:
            return await self.primary.chat(messages, model=model, timeout=timeout, options=options)
        except Exception as exc:
            logger.warning(
                f"Primary AI provider '{self.primary.provider_name}' failed during chat: {str(exc)}. "
                f"Falling back to '{self.fallback.provider_name}'..."
            )
            return await self.fallback.chat(messages, model=model, timeout=timeout, options=options)

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        timeout: float = 30.0,
        options: dict[str, Any] | None = None,
    ) -> AsyncGenerator[str, None]:
        try:
            async for chunk in self.primary.chat_stream(messages, model=model, timeout=timeout, options=options):
                yield chunk
        except Exception as exc:
            logger.warning(
                f"Primary AI streaming provider '{self.primary.provider_name}' failed during chat: {str(exc)}. "
                f"Falling back to '{self.fallback.provider_name}'..."
            )
            async for chunk in self.fallback.chat_stream(messages, model=model, timeout=timeout, options=options):
                yield chunk
