import uuid
from typing import Optional, List
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class Skill(Base, TimestampMixin):
    """
    Skill Master Table — all technical skills taught across branches.
    """
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    course_skills: Mapped[List["CourseSkill"]] = relationship(
        "CourseSkill", back_populates="skill", cascade="all, delete-orphan", lazy="selectin",
    )
