from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.execution_repository import ExecutionRepository
from app.repositories.workflow_repository import WorkflowRepository
from app.schemas.workflow import ExecuteWorkflowRequest, WorkflowCreate, WorkflowUpdate


class WorkflowService:
    def __init__(self, db: Session):
        self.workflows = WorkflowRepository(db)
        self.executions = ExecutionRepository(db)

    def list_workflows(self):
        return self.workflows.list()

    def create_workflow(self, payload: WorkflowCreate, created_by: UUID | None = None):
        return self.workflows.create(payload, created_by)

    def get_workflow(self, workflow_id: UUID):
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        return workflow

    def update_workflow(self, workflow_id: UUID, payload: WorkflowUpdate):
        return self.workflows.update(self.get_workflow(workflow_id), payload)

    def delete_workflow(self, workflow_id: UUID) -> None:
        self.workflows.delete(self.get_workflow(workflow_id))

    def execute_workflow(self, workflow_id: UUID, payload: ExecuteWorkflowRequest):
        workflow = self.get_workflow(workflow_id)
        execution = self.executions.create(workflow.id)
        self.executions.add_log(execution.id, f"Workflow '{workflow.name}' started")

        try:
            for step in sorted(workflow.steps, key=lambda item: item.step_order):
                self.executions.add_log(execution.id, f"Executing {step.step_type} step")
            if not workflow.steps:
                self.executions.add_log(execution.id, "No steps configured; execution completed")
            return self.executions.complete(execution, "completed")
        except Exception as exc:
            self.executions.add_log(execution.id, str(exc), "error")
            return self.executions.complete(execution, "failed")
