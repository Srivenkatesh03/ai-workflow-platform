from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.execution import Execution
from app.models.execution_log import ExecutionLog


class ExecutionRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self) -> list[Execution]:
        return list(self.db.scalars(select(Execution).order_by(Execution.started_at.desc())))

    def get(self, execution_id: UUID) -> Execution | None:
        return self.db.get(Execution, execution_id)

    def create(self, workflow_id: UUID) -> Execution:
        execution = Execution(workflow_id=workflow_id, status="running", started_at=datetime.now(timezone.utc))
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        return execution

    def add_log(self, execution_id: UUID, message: str, level: str = "info") -> ExecutionLog:
        log = ExecutionLog(execution_id=execution_id, log_level=level, message=message)
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def complete(self, execution: Execution, status: str) -> Execution:
        execution.status = status
        execution.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(execution)
        return execution

