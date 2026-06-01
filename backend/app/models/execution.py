import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.mixins import UUIDPrimaryKeyMixin


class Execution(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "executions"

    workflow_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workflows.id"), index=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    workflow: Mapped["Workflow"] = relationship(back_populates="executions")
    logs: Mapped[list["ExecutionLog"]] = relationship(back_populates="execution", cascade="all, delete-orphan")
    step_executions: Mapped[list["StepExecution"]] = relationship(back_populates="execution", cascade="all, delete-orphan")


