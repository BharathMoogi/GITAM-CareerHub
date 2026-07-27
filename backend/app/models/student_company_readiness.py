import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class StudentCompanyReadiness(Base, TimestampMixin):
    """
    Stores calculated readiness metrics for a student against a company / job role.
    Dynamically calculated from student's completed courses, projects, skills, certifications, and roadmap progress.
    """
    __tablename__ = "student_company_readiness"
    __table_args__ = (
        UniqueConstraint("student_id", "company_id", "job_role_id", name="uq_student_company_role_readiness"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    job_role_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("job_roles.id", ondelete="CASCADE"), nullable=True, index=True)

    overall_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False, comment="0-100 score")
    course_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    project_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    skill_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    certification_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    resume_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    interview_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    student: Mapped["Student"] = relationship("Student", lazy="joined")
    company: Mapped["Company"] = relationship("Company", lazy="joined")
    job_role: Mapped[Optional["JobRole"]] = relationship("JobRole", lazy="joined")
