from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional

class BaseExecutionEvent(BaseModel):
    event: str = Field(..., description="The name of the realtime event")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="ISO timestamp of the event occurrence")
    execution_id: UUID = Field(..., description="UUID of the execution")
    workflow_id: UUID = Field(..., description="UUID of the workflow")
    data: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary specific to the event")

class QueueStatePayload(BaseModel):
    redis_connected: bool
    queue_name: str = "celery"
    queue_length: int
    active_workers: int
    error: Optional[str] = None

class QueueStateBroadcast(BaseModel):
    event: str = "queue_updated"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: QueueStatePayload
