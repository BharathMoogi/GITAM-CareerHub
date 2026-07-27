import uuid
from typing import Optional
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class TargetRole(Base, TimestampMixin):
    """
    Target Role Master Model representing career aspirations for engineering students.
    """
    __tablename__ = "target_roles"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    students: Mapped[list["Student"]] = relationship(
        "Student",
        back_populates="target_role",
        lazy="selectin",
    )
