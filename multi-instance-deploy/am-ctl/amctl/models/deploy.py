"""Release and deployment ORM models (Phase 6)."""

from datetime import datetime

from sqlalchemy import BigInteger, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from amctl.models.base import Base


class Release(Base):
    __tablename__ = "releases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    bundle_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    checksum_sha256: Mapped[str] = mapped_column(Text, nullable=False)
    artifact_hashes: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Deployment(Base):
    __tablename__ = "deployments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    agent_id: Mapped[int] = mapped_column(Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    release_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("releases.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    detail: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    deployed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
