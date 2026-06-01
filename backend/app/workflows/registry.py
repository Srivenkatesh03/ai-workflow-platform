import logging
from typing import Any
from app.workflows.base import BaseStepHandler

logger = logging.getLogger(__name__)


class StepHandlerRegistry:
    _handlers: dict[str, type[BaseStepHandler]] = {}

    @classmethod
    def register(cls, step_type: str):
        """Decorator to register a step handler class."""
        def decorator(handler_cls: type[BaseStepHandler]):
            cls._handlers[step_type] = handler_cls
            return handler_cls
        return decorator

    @classmethod
    def get_handler(cls, step_type: str) -> BaseStepHandler:
        """Instantiates and returns the step handler for a given step type."""
        handler_cls = cls._handlers.get(step_type)
        if not handler_cls:
            raise ValueError(f"No step handler registered for type: {step_type}")
        return handler_cls()
