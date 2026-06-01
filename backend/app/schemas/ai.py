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

