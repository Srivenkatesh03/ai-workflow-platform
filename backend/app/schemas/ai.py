from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field


class SummarizeRequest(BaseModel):
    text: str = Field(min_length=1)
    provider: str = "local"


class ClassifyRequest(BaseModel):
    text: str = Field(min_length=1)
    labels: list[str] = Field(min_length=1)
    provider: str = "local"


class AIResult(BaseModel):
    provider: str
    model: str
    output: str
    usage: dict[str, int]


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1)
    provider: str | None = None
    model: str | None = None
    timeout: float = 30.0
    options: dict[str, Any] | None = None
    workflow_id: UUID | None = None
    execution_id: UUID | None = None


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant|system)$")
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1)
    provider: str | None = None
    model: str | None = None
    timeout: float = 30.0
    options: dict[str, Any] | None = None
    workflow_id: UUID | None = None
    execution_id: UUID | None = None


