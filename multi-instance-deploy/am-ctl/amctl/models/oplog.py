"""Operational run and stage rows. These are not audit_log rows."""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from amctl.models.base import Base

ACTIONS = (
    "create",
    "teardown",
    "health_check",
    "repair",
    "release",
    "backup",
    "credential_check",
    "model_change",
)


class OperationalRun(Base):
    __tablename__ = "operational_runs"

    run_id: Mapped[str] = mapped_column(Text, primary_key=True)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    target: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor: Mapped[str] = mapped_column(Text, nullable=False)
    writer_pid: Mapped[int | None] = mapped_column(Integer, nullable=True)
    outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    stages: Mapped[list["OperationalStage"]] = relationship(
        back_populates="run",
        order_by="OperationalStage.id",
    )


class OperationalStage(Base):
    __tablename__ = "operational_stages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("operational_runs.run_id", ondelete="CASCADE"),
        nullable=False,
    )
    stage: Mapped[str] = mapped_column(Text, nullable=False)
    phase: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    exit_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stdout_tail: Mapped[str | None] = mapped_column(Text, nullable=True)
    stderr_tail: Mapped[str | None] = mapped_column(Text, nullable=True)
    truncated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    instance_present: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    run: Mapped[OperationalRun] = relationship(back_populates="stages")
