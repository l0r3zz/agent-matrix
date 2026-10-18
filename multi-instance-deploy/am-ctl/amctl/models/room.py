"""Required room membership ORM model."""

from sqlalchemy import Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from amctl.models.base import Base


class RequiredRoom(Base):
    __tablename__ = "required_rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[int] = mapped_column(Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    room_id: Mapped[str] = mapped_column(Text, nullable=False)
    room_name: Mapped[str | None] = mapped_column(Text, nullable=True)

    agent = relationship("Agent", back_populates="required_rooms")
