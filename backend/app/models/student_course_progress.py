import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class StudentCourseProgress(Base, TimestampMixin):
    """
    Tracks a student's progress through each Course.
    """
    __tablename__ = "student_course_progress"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_student_course_progress"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="NOT_STARTED", nullable=False, comment="NOT_STARTED, IN_PROGRESS, COMPLETED")
    completion_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    student: Mapped["Student"] = relationship("Student", lazy="joined")
    course: Mapped["Course"] = relationship("Course", lazy="joined")
