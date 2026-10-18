"""Agent registry ORM model."""

from datetime import datetime

from sqlalchemy import Integer, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from amctl.models.base import Base


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instance_num: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    matrix_user_id: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    homeserver_url: Mapped[str] = mapped_column(Text, nullable=False)
    homeserver_fqdn: Mapped[str] = mapped_column(Text, nullable=False)
    agent_zero_endpoint: Mapped[str] = mapped_column(Text, nullable=False, default="http://localhost:80")
    bot_runtime: Mapped[str] = mapped_column(Text, nullable=False, default="rust")
    status: Mapped[str] = mapped_column(Text, nullable=False, default="active")
    release_version: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    required_rooms = relationship("RequiredRoom", back_populates="agent", lazy="selectin")
    credential_fingerprints = relationship("CredentialFingerprint", back_populates="agent", lazy="selectin")
