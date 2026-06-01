import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ExecutionLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "execution_logs"

    execution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("executions.id"), index=True)
    log_level: Mapped[str] = mapped_column(String(20), default="info")
    message: Mapped[str] = mapped_column(Text)

    execution: Mapped["Execution"] = relationship(back_populates="logs")

