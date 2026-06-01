import time
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.integrations.ai.base import FallbackAIProvider, estimate_tokens
from app.integrations.ai.local import LocalAIProvider
from app.integrations.ai.mock import MockAIProvider
from app.integrations.ai.ollama import OllamaAIProvider
from app.models.ai_log import AILog
from app.schemas.ai import AIResult


class AIService:
    """
    Modular, provider-independent service layer that orchestrates AI providers,
    coordinates local failover chains, resolves environment bindings, and logs metric history.
    """

    def __init__(self, db: Session | None = None):
        self.db = db
        settings = get_settings()

        # Initialize concrete adapters
        mock_provider = MockAIProvider(model=settings.mock_model)
        local_provider = LocalAIProvider()
        ollama_provider = OllamaAIProvider(base_url=settings.ollama_base_url, default_model=settings.ollama_model)

        self.providers = {
            "mock": mock_provider,
            "local": local_provider,
            "ollama": ollama_provider,
        }

        # Setup standard active execution pipeline with resilience fallback chains
        if settings.ai_provider == "ollama":
            self.active_provider = FallbackAIProvider(primary=ollama_provider, fallback=mock_provider)
        elif settings.ai_provider == "mock":
            self.active_provider = mock_provider
        else:
            self.active_provider = local_provider

    async def generate(
        self,
        prompt: str,
        provider: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
        options: dict[str, Any] | None = None,
        workflow_id: UUID | None = None,
        execution_id: UUID | None = None,
    ) -> AIResult:
        adapter = self.providers.get(provider) if provider else self.active_provider
        if not adapter:
            adapter = self.active_provider

        start_time = time.perf_counter()
        success = True
        error_msg = None
        result = None

        try:
            result = await adapter.generate(prompt, model=model, timeout=timeout, options=options)
            return AIResult(
                provider=result.provider,
                model=result.model,
                output=result.output,
                usage=result.usage,
            )
        except Exception as exc:
            success = False
            error_msg = str(exc)
            raise exc
        finally:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            if self.db:
                prompt_tokens = estimate_tokens(prompt)
                completion_tokens = estimate_tokens(result.output) if result else 0
                log_record = AILog(
                    provider=result.provider if result else (provider or adapter.provider_name),
                    model=result.model if result else (model or adapter.default_model),
                    prompt_tokens=result.usage.get("prompt_tokens", prompt_tokens) if result else prompt_tokens,
                    completion_tokens=result.usage.get("completion_tokens", completion_tokens) if result else completion_tokens,
                    total_tokens=result.usage.get("total_tokens", prompt_tokens + completion_tokens) if result else (prompt_tokens + completion_tokens),
                    response_time_ms=result.latency_ms if result else latency_ms,
                    workflow_id=workflow_id,
                    execution_id=execution_id,
                    success=success,
                    error_message=error_msg,
                )
                self.db.add(log_record)
                self.db.commit()
                self.db.refresh(log_record)

    async def chat(
        self,
        messages: list[dict[str, str]],
        provider: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
        options: dict[str, Any] | None = None,
        workflow_id: UUID | None = None,
        execution_id: UUID | None = None,
    ) -> AIResult:
        adapter = self.providers.get(provider) if provider else self.active_provider
        if not adapter:
            adapter = self.active_provider

        start_time = time.perf_counter()
        success = True
        error_msg = None
        result = None

        try:
            result = await adapter.chat(messages, model=model, timeout=timeout, options=options)
            return AIResult(
                provider=result.provider,
                model=result.model,
                output=result.output,
                usage=result.usage,
            )
        except Exception as exc:
            success = False
            error_msg = str(exc)
            raise exc
        finally:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            if self.db:
                prompt_tokens = sum(estimate_tokens(m.get("content", "")) for m in messages)
                completion_tokens = estimate_tokens(result.output) if result else 0
                log_record = AILog(
                    provider=result.provider if result else (provider or adapter.provider_name),
                    model=result.model if result else (model or adapter.default_model),
                    prompt_tokens=result.usage.get("prompt_tokens", prompt_tokens) if result else prompt_tokens,
                    completion_tokens=result.usage.get("completion_tokens", completion_tokens) if result else completion_tokens,
                    total_tokens=result.usage.get("total_tokens", prompt_tokens + completion_tokens) if result else (prompt_tokens + completion_tokens),
                    response_time_ms=result.latency_ms if result else latency_ms,
                    workflow_id=workflow_id,
                    execution_id=execution_id,
                    success=success,
                    error_message=error_msg,
                )
                self.db.add(log_record)
                self.db.commit()
                self.db.refresh(log_record)

    async def summarize(
        self,
        text: str,
        provider: str | None = None,
        workflow_source: str | None = None,
        execution_id: UUID | None = None,
        workflow_id: UUID | None = None,
    ) -> AIResult:
        adapter = self.providers.get(provider) if provider else self.active_provider
        if not adapter:
            adapter = self.active_provider

        start_time = time.perf_counter()
        success = True
        error_msg = None
        result = None

        try:
            result = await adapter.summarize(text)
            return AIResult(provider=result.provider, model=result.model, output=result.output, usage=result.usage)
        except Exception as exc:
            success = False
            error_msg = str(exc)
            raise exc
        finally:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            if self.db:
                prompt_tokens = estimate_tokens(text)
                completion_tokens = estimate_tokens(result.output) if result else 0
                log_record = AILog(
                    provider=result.provider if result else (provider or adapter.provider_name),
                    model=result.model if result else (adapter.default_model),
                    prompt_tokens=result.usage.get("prompt_tokens", prompt_tokens) if result else prompt_tokens,
                    completion_tokens=result.usage.get("completion_tokens", completion_tokens) if result else completion_tokens,
                    total_tokens=result.usage.get("total_tokens", prompt_tokens + completion_tokens) if result else (prompt_tokens + completion_tokens),
                    response_time_ms=result.latency_ms if result else latency_ms,
                    workflow_source=workflow_source,
                    execution_id=execution_id,
                    workflow_id=workflow_id,
                    success=success,
                    error_message=error_msg,
                )
                self.db.add(log_record)
                self.db.commit()
                self.db.refresh(log_record)

    async def classify(
        self,
        text: str,
        labels: list[str],
        provider: str | None = None,
        workflow_source: str | None = None,
        execution_id: UUID | None = None,
        workflow_id: UUID | None = None,
    ) -> AIResult:
        adapter = self.providers.get(provider) if provider else self.active_provider
        if not adapter:
            adapter = self.active_provider

        start_time = time.perf_counter()
        success = True
        error_msg = None
        result = None

        try:
            result = await adapter.classify(text, labels)
            return AIResult(provider=result.provider, model=result.model, output=result.output, usage=result.usage)
        except Exception as exc:
            success = False
            error_msg = str(exc)
            raise exc
        finally:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            if self.db:
                prompt_tokens = estimate_tokens(text)
                completion_tokens = estimate_tokens(result.output) if result else 0
                log_record = AILog(
                    provider=result.provider if result else (provider or adapter.provider_name),
                    model=result.model if result else (adapter.default_model),
                    prompt_tokens=result.usage.get("prompt_tokens", prompt_tokens) if result else prompt_tokens,
                    completion_tokens=result.usage.get("completion_tokens", completion_tokens) if result else completion_tokens,
                    total_tokens=result.usage.get("total_tokens", prompt_tokens + completion_tokens) if result else (prompt_tokens + completion_tokens),
                    response_time_ms=result.latency_ms if result else latency_ms,
                    workflow_source=workflow_source,
                    execution_id=execution_id,
                    workflow_id=workflow_id,
                    success=success,
                    error_message=error_msg,
                )
                self.db.add(log_record)
                self.db.commit()
                self.db.refresh(log_record)

