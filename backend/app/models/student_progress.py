import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class StudentRoadmapProgress(Base, TimestampMixin):
    """
    Tracks individual student progress for each roadmap module.
    Statuses: NOT_STARTED, IN_PROGRESS, COMPLETED, SKIPPED
    """
    __tablename__ = "student_roadmap_progress"
    __table_args__ = (
        UniqueConstraint("student_id", "roadmap_module_id", name="uq_student_module_progress"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    student_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    roadmap_module_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("roadmap_modules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="NOT_STARTED",
        nullable=False,
        comment="NOT_STARTED, IN_PROGRESS, COMPLETED, SKIPPED",
    )
    completion_percentage: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    student: Mapped["Student"] = relationship("Student", lazy="joined")
    roadmap_module: Mapped["RoadmapModule"] = relationship("RoadmapModule", lazy="joined")
