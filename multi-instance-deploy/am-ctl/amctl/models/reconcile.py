"""Reconciliation run ORM model (Phase 4)."""

from datetime import datetime

from sqlalchemy import BigInteger, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from amctl.models.base import Base


class ReconcileRun(Base):
    __tablename__ = "reconcile_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    agent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=True)
    mode: Mapped[str] = mapped_column(Text, nullable=False)
    result: Mapped[dict] = mapped_column(JSONB, nullable=False)
    operator: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
