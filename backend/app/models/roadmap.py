import uuid
from typing import Optional, List
from sqlalchemy import String, Text, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class Roadmap(Base, TimestampMixin):
    """
    Roadmap Model representing curriculum map per Branch & Semester.
    """
    __tablename__ = "roadmaps"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    branch_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("branches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    academic_year_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    semester_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("semesters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relationships
    branch: Mapped["Branch"] = relationship("Branch", lazy="joined")
    academic_year: Mapped["AcademicYear"] = relationship("AcademicYear", lazy="joined")
    semester: Mapped["Semester"] = relationship("Semester", lazy="joined")
    modules: Mapped[List["RoadmapModule"]] = relationship(
        "RoadmapModule",
        back_populates="roadmap",
        cascade="all, delete-orphan",
        order_by="RoadmapModule.display_order",
        lazy="joined",
    )
