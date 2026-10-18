"""Credential fingerprint and trusted sender ORM models."""

from datetime import datetime

from sqlalchemy import Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from amctl.models.base import Base


class CredentialFingerprint(Base):
    __tablename__ = "credential_fingerprints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[int] = mapped_column(Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    domain: Mapped[str] = mapped_column(Text, nullable=False)
    fingerprint: Mapped[str] = mapped_column(Text, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    agent = relationship("Agent", back_populates="credential_fingerprints")


class TrustedSender(Base):
    __tablename__ = "trusted_senders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    matrix_user_id: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    trust_level: Mapped[str] = mapped_column(Text, nullable=False, default="fleet_member")
