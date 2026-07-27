import uuid
from typing import Optional
from sqlalchemy import String, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class CompanySkill(Base, TimestampMixin):
    """Company skill mapping with required level and weightage."""
    __tablename__ = "company_skills"
    __table_args__ = (
        UniqueConstraint("company_id", "skill_id", name="uq_company_skill"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id: Mapped[str] = mapped_column(String(36), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    required_level: Mapped[str] = mapped_column(String(50), default="BEGINNER", nullable=False)
    weightage: Mapped[float] = mapped_column(Float, default=1.0, nullable=False, comment="Relative weight for readiness score")

    company: Mapped["Company"] = relationship("Company", back_populates="company_skills")
    skill: Mapped["Skill"] = relationship("Skill", lazy="joined")


class CompanyCourse(Base, TimestampMixin):
    """Company recommended course."""
    __tablename__ = "company_courses"
    __table_args__ = (
        UniqueConstraint("company_id", "course_id", name="uq_company_course"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    importance: Mapped[str] = mapped_column(String(50), default="HIGH", nullable=False, comment="CRITICAL, HIGH, MEDIUM, OPTIONAL")

    company: Mapped["Company"] = relationship("Company", back_populates="recommended_courses")
    course: Mapped["Course"] = relationship("Course", lazy="joined")


class CompanyProject(Base, TimestampMixin):
    """Company recommended project."""
    __tablename__ = "company_projects"
    __table_args__ = (
        UniqueConstraint("company_id", "project_id", name="uq_company_project"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    importance: Mapped[str] = mapped_column(String(50), default="HIGH", nullable=False, comment="CRITICAL, HIGH, MEDIUM, OPTIONAL")

    company: Mapped["Company"] = relationship("Company", back_populates="recommended_projects")
    project: Mapped["Project"] = relationship("Project", lazy="joined")


class CompanyCertification(Base, TimestampMixin):
    """Company recommended certification."""
    __tablename__ = "company_certifications"
    __table_args__ = (
        UniqueConstraint("company_id", "certification_id", name="uq_company_certification"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    certification_id: Mapped[str] = mapped_column(String(36), ForeignKey("certifications.id", ondelete="CASCADE"), nullable=False, index=True)
    importance: Mapped[str] = mapped_column(String(50), default="HIGH", nullable=False, comment="CRITICAL, HIGH, MEDIUM, OPTIONAL")

    company: Mapped["Company"] = relationship("Company", back_populates="recommended_certifications")
    certification: Mapped["Certification"] = relationship("Certification", lazy="joined")
