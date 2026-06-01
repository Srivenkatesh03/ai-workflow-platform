from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ExecutionLogRead(BaseModel):
    id: UUID
    log_level: str
    message: str
    created_at: datetime

    model_config = {"from_attributes": True}


class StepExecutionRead(BaseModel):
    id: UUID
    execution_id: UUID
    step_id: UUID
    status: str
    failure_reason: str | None = None
    retry_count: int = 0
    duration_sec: float | None = None
    results: dict | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class ExecutionRead(BaseModel):
    id: UUID
    workflow_id: UUID
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    step_executions: list[StepExecutionRead] = []

    model_config = {"from_attributes": True}


