from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.workflow import Workflow
from app.models.workflow_step import WorkflowStep
from app.schemas.workflow import WorkflowCreate, WorkflowUpdate


class WorkflowRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self) -> list[Workflow]:
        return list(self.db.scalars(select(Workflow).order_by(Workflow.created_at.desc())))

    def get(self, workflow_id: UUID) -> Workflow | None:
        return self.db.get(Workflow, workflow_id)

    def create(self, payload: WorkflowCreate, created_by: UUID | None = None) -> Workflow:
        workflow = Workflow(
            name=payload.name,
            description=payload.description,
            trigger_type=payload.trigger_type,
            status="pending",
            created_by=created_by,
        )
        for step in payload.steps:
            workflow.steps.append(
                WorkflowStep(
                    step_order=step.step_order,
                    step_type=step.step_type,
                    configuration=step.configuration,
                )
            )
        self.db.add(workflow)
        self.db.commit()
        self.db.refresh(workflow)
        return workflow

    def update(self, workflow: Workflow, payload: WorkflowUpdate) -> Workflow:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(workflow, field, value)
        self.db.commit()
        self.db.refresh(workflow)
        return workflow

    def delete(self, workflow: Workflow) -> None:
        self.db.delete(workflow)
        self.db.commit()
