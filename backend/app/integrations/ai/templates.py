import re
from typing import Any, Dict, Set


class PromptTemplateError(Exception):
    """Raised when prompt rendering fails due to validation errors."""
    pass


class PromptTemplate:
    """
    Represents a prompt template that supports static/dynamic variable formatting
    with strict validation of placeholders.
    """

    def __init__(self, name: str, template: str, required_keys: Set[str] | None = None):
        self.name = name
        self.template = template
        # Automatically detect required keys if not specified
        if required_keys is None:
            self.required_keys = self._detect_placeholders(template)
        else:
            self.required_keys = required_keys

    def _detect_placeholders(self, template: str) -> Set[str]:
        """Detects standard python format placeholders like {variable}."""
        # Find all {...} occurrences but ignore double braces {{...}} which format as literal braces
        pattern = re.compile(r"(?<!{){([a-zA-Z0-9_]+)}(?!})")
        return set(pattern.findall(template))

    def render(self, **kwargs: Any) -> str:
        """
        Renders the prompt template with provided variables.
        Validates that all required keys are supplied.
        """
        missing_keys = self.required_keys - set(kwargs.keys())
        if missing_keys:
            raise PromptTemplateError(
                f"Missing required variables for template '{self.name}': {', '.join(missing_keys)}"
            )
        try:
            return self.template.format(**kwargs)
        except Exception as exc:
            raise PromptTemplateError(f"Failed to render template '{self.name}': {str(exc)}")


class PromptTemplateManager:
    """
    Manages loading, registering, and retrieving reusable prompt templates.
    """

    def __init__(self):
        self._templates: Dict[str, PromptTemplate] = {}
        self._register_default_templates()

    def register(self, template: PromptTemplate) -> None:
        """Registers a new template in the system."""
        self._templates[template.name] = template

    def get(self, name: str) -> PromptTemplate:
        """Retrieves a registered template by name."""
        if name not in self._templates:
            raise KeyError(f"Prompt template '{name}' is not registered.")
        return self._templates[name]

    def render_template(self, template_name: str, **kwargs: Any) -> str:
        """Retrieves and renders a template in one call."""
        return self.get(template_name).render(**kwargs)

    def _register_default_templates(self) -> None:
        """Registers the system's foundational default templates."""
        # Summarize Template
        self.register(
            PromptTemplate(
                name="summarize",
                template=(
                    "Summarize the following text concisely. Keep it under 40 words:\n\n"
                    "Text: {text}"
                ),
            )
        )

        # Classify Template
        self.register(
            PromptTemplate(
                name="classify",
                template=(
                    "Classify the following text into exactly one of these categories: [{categories}].\n"
                    "Respond with ONLY the exact matching category name and absolutely nothing else.\n\n"
                    "Text: {text}"
                ),
            )
        )

        # Entity Extraction Template
        self.register(
            PromptTemplate(
                name="extract_entities",
                template=(
                    "Analyze the following text and extract all entities of type: [{entity_types}].\n"
                    "Return the result as a clean JSON list of strings.\n\n"
                    "Text: {text}"
                ),
            )
        )

        # Sentiment Analysis Template
        self.register(
            PromptTemplate(
                name="sentiment",
                template=(
                    "Analyze the sentiment of the following text.\n"
                    "Respond with exactly one of: [POSITIVE, NEGATIVE, NEUTRAL].\n\n"
                    "Text: {text}"
                ),
            )
        )


# Global instance of the template manager
prompt_templates = PromptTemplateManager()
