import uuid
from typing import Optional, List
from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class Project(Base, TimestampMixin):
    """
    Project model — each project is scoped to a Branch, Year, Semester and
    optionally linked to a RoadmapModule for auto-unlock logic.
    """
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    roadmap_module_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("roadmap_modules.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    problem_statement: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    real_world_impact: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    difficulty: Mapped[str] = mapped_column(String(50), default="BEGINNER", nullable=False)
    estimated_duration: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="e.g. '2 weeks', '1 month'")
    branch_id: Mapped[str] = mapped_column(String(36), ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id: Mapped[str] = mapped_column(String(36), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)
    semester_id: Mapped[str] = mapped_column(String(36), ForeignKey("semesters.id", ondelete="CASCADE"), nullable=False, index=True)
    project_type: Mapped[str] = mapped_column(
        String(50), default="MINI", nullable=False,
        comment="MINI, MINOR, MAJOR, CAPSTONE",
    )
    status: Mapped[str] = mapped_column(String(50), default="PUBLISHED", nullable=False, comment="DRAFT, PUBLISHED, ARCHIVED")
    thumbnail: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    branch: Mapped["Branch"] = relationship("Branch", lazy="joined")
    academic_year: Mapped["AcademicYear"] = relationship("AcademicYear", lazy="joined")
    semester: Mapped["Semester"] = relationship("Semester", lazy="joined")
    roadmap_module: Mapped[Optional["RoadmapModule"]] = relationship("RoadmapModule", lazy="joined")

    project_skills: Mapped[List["ProjectSkill"]] = relationship(
        "ProjectSkill", back_populates="project", cascade="all, delete-orphan", lazy="joined",
    )
    technology_maps: Mapped[List["ProjectTechnologyMap"]] = relationship(
        "ProjectTechnologyMap", back_populates="project", cascade="all, delete-orphan", lazy="joined",
    )
    resources: Mapped[List["ProjectResource"]] = relationship(
        "ProjectResource", back_populates="project", cascade="all, delete-orphan",
        order_by="ProjectResource.display_order", lazy="joined",
    )
    deliverables: Mapped[List["ProjectDeliverable"]] = relationship(
        "ProjectDeliverable", back_populates="project", cascade="all, delete-orphan",
        order_by="ProjectDeliverable.display_order", lazy="joined",
    )
    interview_questions: Mapped[List["ProjectInterviewQuestion"]] = relationship(
        "ProjectInterviewQuestion", back_populates="project", cascade="all, delete-orphan", lazy="joined",
    )
    resume_points: Mapped[List["ProjectResumePoint"]] = relationship(
        "ProjectResumePoint", back_populates="project", cascade="all, delete-orphan",
        order_by="ProjectResumePoint.display_order", lazy="joined",
    )
