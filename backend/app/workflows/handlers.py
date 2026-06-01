import logging
import re
from datetime import datetime, timezone
from typing import Any

import httpx

from app.models.notification import Notification
from app.services.ai_service import AIService
from app.workflows.base import BaseStepHandler
from app.workflows.registry import StepHandlerRegistry

logger = logging.getLogger(__name__)


def resolve_path(path: str, context: dict[str, Any]) -> Any:
    """
    Resolves a dot-separated path from the context.
    E.g. "payload.text" -> context["payload"]["text"]
    """
    parts = path.strip().split(".")
    current = context
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def resolve_templates(val: Any, context: dict[str, Any]) -> Any:
    """
    Recursively resolves dynamic values in string, list, or dict templates.
    Supports exact objects: "{{ payload.data }}" -> returns the typed object directly.
    Supports embedded placeholders: "Total is: {{ payload.total }} USD" -> string interpolation.
    """
    if isinstance(val, str):
        # Exact match
        if val.startswith("{{") and val.endswith("}}"):
            path = val[2:-2].strip()
            res = resolve_path(path, context)
            if res is not None:
                return res

        # Embedded placeholders
        def replacer(match):
            path = match.group(1).strip()
            res = resolve_path(path, context)
            return str(res) if res is not None else ""

        return re.sub(r"\{\{([^}]+)\}\}", replacer, val)

    elif isinstance(val, list):
        return [resolve_templates(item, context) for item in val]
    elif isinstance(val, dict):
        return {k: resolve_templates(v, context) for k, v in val.items()}
    return val


@StepHandlerRegistry.register("ai_summarize")
class AISummarizeHandler(BaseStepHandler):
    async def execute(self, config: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        text_template = config.get("text", "")
        provider = config.get("provider", "local")

        resolved_text = resolve_templates(text_template, context)
        if not resolved_text:
            raise ValueError("Input 'text' is missing or resolved to empty string in ai_summarize step")

        ai_service = AIService(db=context.get("db"))
        result = await ai_service.summarize(
            resolved_text,
            provider=provider,
            workflow_source=context.get("workflow_source"),
            execution_id=context.get("execution_id"),
        )

        return {
            "summary": result.output,
            "provider": result.provider,
            "model": result.model,
            "usage": result.usage,
        }


@StepHandlerRegistry.register("ai_classify")
class AIClassifyHandler(BaseStepHandler):
    async def execute(self, config: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        text_template = config.get("text", "")
        labels_template = config.get("labels", [])
        provider = config.get("provider", "local")

        resolved_text = resolve_templates(text_template, context)
        resolved_labels = resolve_templates(labels_template, context)

        if not resolved_text:
            raise ValueError("Input 'text' is missing or resolved to empty string in ai_classify step")
        if not resolved_labels or not isinstance(resolved_labels, list):
            raise ValueError("Input 'labels' must be a non-empty list of classification categories")

        # Convert all elements in labels to string
        labels = [str(lbl) for lbl in resolved_labels]

        ai_service = AIService(db=context.get("db"))
        result = await ai_service.classify(
            resolved_text,
            labels,
            provider=provider,
            workflow_source=context.get("workflow_source"),
            execution_id=context.get("execution_id"),
        )


        return {
            "category": result.output,
            "provider": result.provider,
            "model": result.model,
            "usage": result.usage,
        }


@StepHandlerRegistry.register("notify")
class NotifyHandler(BaseStepHandler):
    async def execute(self, config: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        channel = config.get("channel", "email")
        recipient_template = config.get("recipient", "")
        message_template = config.get("message", "")

        resolved_recipient = resolve_templates(recipient_template, context)
        resolved_message = resolve_templates(message_template, context)

        if not resolved_recipient:
            raise ValueError("Recipient address/channel is missing in notify step")
        if not resolved_message:
            raise ValueError("Message body is missing in notify step")

        db = context.get("db")
        if db:
            # Create a persistent notification record in the database
            notif = Notification(
                channel=channel,
                recipient=resolved_recipient,
                status="sent",
                sent_at=datetime.now(timezone.utc),
            )
            db.add(notif)
            db.commit()
            db.refresh(notif)

        logger.info(f"Notification sent via {channel} to {resolved_recipient}: {resolved_message}")

        return {
            "channel": channel,
            "recipient": resolved_recipient,
            "message": resolved_message,
            "status": "sent",
        }


@StepHandlerRegistry.register("webhook_call")
class WebhookCallHandler(BaseStepHandler):
    async def execute(self, config: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        url_template = config.get("url", "")
        payload_template = config.get("payload", {})
        headers_template = config.get("headers", {})

        resolved_url = resolve_templates(url_template, context)
        resolved_payload = resolve_templates(payload_template, context)
        resolved_headers = resolve_templates(headers_template, context)

        if not resolved_url:
            raise ValueError("Webhook 'url' is missing in webhook_call step")

        headers = {str(k): str(v) for k, v in resolved_headers.items()} if resolved_headers else {}

        # Default payload to execution context payload if not specified
        payload = resolved_payload if resolved_payload is not None else {}

        async with httpx.AsyncClient() as client:
            response = await client.post(resolved_url, json=payload, headers=headers, timeout=10.0)

            # Automatically trigger exception on error so that step retry/failure logic can handle it
            response.raise_for_status()

            try:
                response_body = response.json()
            except Exception:
                response_body = response.text

            return {
                "status_code": response.status_code,
                "response_body": response_body,
                "success": True,
            }


@StepHandlerRegistry.register("approval")
class ApprovalPlaceholderHandler(BaseStepHandler):
    async def execute(self, config: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        message_template = config.get("message", "Approval requested")
        resolved_message = resolve_templates(message_template, context)

        logger.info(f"Approval request registered: {resolved_message}")

        return {
            "status": "approved",
            "message": resolved_message,
            "details": "Simulated automatic approval for placeholder handler",
        }
