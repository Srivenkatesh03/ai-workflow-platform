from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ExecutionLogRead(BaseModel):
    id: UUID
    log_level: str
    message: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ExecutionRead(BaseModel):
    id: UUID
    workflow_id: UUID
    status: str
    started_at: datetime | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}

