import uuid
from typing import Optional, List
from sqlalchemy import String, Text, Integer, Boolean, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class Course(Base, TimestampMixin):
    """
    Course Model — each course maps to a RoadmapModule and delivers structured learning.
    """
    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    roadmap_module_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("roadmap_modules.id", ondelete="SET NULL"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    branch_id: Mapped[str] = mapped_column(String(36), ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id: Mapped[str] = mapped_column(String(36), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)
    semester_id: Mapped[str] = mapped_column(String(36), ForeignKey("semesters.id", ondelete="CASCADE"), nullable=False, index=True)
    difficulty: Mapped[str] = mapped_column(String(50), default="BEGINNER", nullable=False, comment="BEGINNER, INTERMEDIATE, ADVANCED")
    estimated_hours: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    thumbnail: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    learning_objectives: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prerequisites: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="PUBLISHED", nullable=False, comment="DRAFT, PUBLISHED, ARCHIVED")

    # Relationships
    branch: Mapped["Branch"] = relationship("Branch", lazy="joined")
    academic_year: Mapped["AcademicYear"] = relationship("AcademicYear", lazy="joined")
    semester: Mapped["Semester"] = relationship("Semester", lazy="joined")
    roadmap_module: Mapped[Optional["RoadmapModule"]] = relationship("RoadmapModule", lazy="joined")

    resources: Mapped[List["CourseResource"]] = relationship(
        "CourseResource", back_populates="course",
        cascade="all, delete-orphan", order_by="CourseResource.display_order", lazy="joined",
    )
    outcomes: Mapped[List["CourseOutcome"]] = relationship(
        "CourseOutcome", back_populates="course",
        cascade="all, delete-orphan", order_by="CourseOutcome.display_order", lazy="joined",
    )
    course_skills: Mapped[List["CourseSkill"]] = relationship(
        "CourseSkill", back_populates="course",
        cascade="all, delete-orphan", lazy="joined",
    )
