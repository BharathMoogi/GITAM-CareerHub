import uuid
from typing import Optional, List
from sqlalchemy import String, Text, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class ProjectTechnology(Base, TimestampMixin):
    """Master table of technologies used across projects."""
    __tablename__ = "project_technologies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    technology_maps: Mapped[List["ProjectTechnologyMap"]] = relationship(
        "ProjectTechnologyMap", back_populates="technology", cascade="all, delete-orphan", lazy="selectin",
    )
