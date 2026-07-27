import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class StudentProject(Base, TimestampMixin):
    """
    Tracks a student's work on a specific project.
    Stores submission artifacts and review score for future AI reviewer integration.
    """
    __tablename__ = "student_projects"
    __table_args__ = (
        UniqueConstraint("student_id", "project_id", name="uq_student_project"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(50), default="NOT_STARTED", nullable=False,
        comment="NOT_STARTED, IN_PROGRESS, SUBMITTED, COMPLETED",
    )

    # Submission artifacts — schema-ready for future AI reviewer
    github_repository: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    demo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    report_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    submission_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Review score — populated by future AI review engine
    review_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="AI review score 0-100")

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    student: Mapped["Student"] = relationship("Student", lazy="joined")
    project: Mapped["Project"] = relationship("Project", lazy="joined")
