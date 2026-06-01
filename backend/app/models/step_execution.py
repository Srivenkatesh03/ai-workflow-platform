import uuid
from datetime import datetime

from sqlalchemy import Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class StepExecution(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "step_executions"

    execution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("executions.id", ondelete="CASCADE"), index=True)
    step_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workflow_steps.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    duration_sec: Mapped[float | None] = mapped_column(Float, nullable=True)
    results: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    execution: Mapped["Execution"] = relationship(back_populates="step_executions")
    step: Mapped["WorkflowStep"] = relationship()
