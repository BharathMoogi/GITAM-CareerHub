import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class StudentSkill(Base, TimestampMixin):
    """
    A student's acquired skill score — updated automatically when courses are completed.
    """
    __tablename__ = "student_skills"
    __table_args__ = (
        UniqueConstraint("student_id", "skill_id", name="uq_student_skill"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id: Mapped[str] = mapped_column(String(36), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    proficiency_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False, comment="0-100 score")
    earned_from_course_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("courses.id", ondelete="SET NULL"), nullable=True)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    student: Mapped["Student"] = relationship("Student", lazy="joined")
    skill: Mapped["Skill"] = relationship("Skill", lazy="joined")
    earned_from_course: Mapped[Optional["Course"]] = relationship("Course", lazy="joined")
