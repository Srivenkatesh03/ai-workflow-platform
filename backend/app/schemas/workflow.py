from uuid import UUID

from pydantic import BaseModel, Field


class WorkflowStepCreate(BaseModel):
    step_order: int = Field(ge=1)
    step_type: str = Field(min_length=2, max_length=50)
    configuration: dict = Field(default_factory=dict)


class WorkflowCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str | None = None
    trigger_type: str = Field(default="manual", min_length=2, max_length=50)
    steps: list[WorkflowStepCreate] = Field(default_factory=list)


class WorkflowUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = None
    trigger_type: str | None = Field(default=None, min_length=2, max_length=50)
    status: str | None = Field(default=None, min_length=2, max_length=50)


class WorkflowRead(BaseModel):
    id: UUID
    name: str
    description: str | None
    trigger_type: str
    status: str

    model_config = {"from_attributes": True}


class ExecuteWorkflowRequest(BaseModel):
    payload: dict = Field(default_factory=dict)

