"""
Internship & Placement Engine — SQLAlchemy Models.

Tables:
- Internship          : Internship postings tied to company + job_role
- PlacementJob        : Full-time placement jobs
- StudentApplication  : Tracks student applications with stage pipeline
- InterviewSchedule   : Scheduled interview rounds per application
- OfferLetter         : Offer letter records on selection
"""
import uuid
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    String, Text, Integer, Float, Boolean,
    Date, DateTime, ForeignKey, UniqueConstraint, Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


# ─── Enums ────────────────────────────────────────────────────────────────────

APPLICATION_STATUS = (
    "SAVED", "APPLIED", "SHORTLISTED",
    "ONLINE_TEST", "TECHNICAL", "HR",
    "SELECTED", "REJECTED",
)

INTERNSHIP_TYPES = ("TECHNICAL", "RESEARCH", "MANAGEMENT", "DESIGN", "DATA")
INTERNSHIP_MODES = ("REMOTE", "HYBRID", "ONSITE")
OFFER_TYPES      = ("INTERNSHIP", "PLACEMENT")


# ─── Internship ───────────────────────────────────────────────────────────────

class Internship(Base, TimestampMixin):
    """
    Internship posting offered by a company.
    Eligibility rules enforce minimum readiness score.
    """
    __tablename__ = "internships"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    job_role_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("job_roles.id", ondelete="SET NULL"), nullable=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    internship_type: Mapped[str] = mapped_column(String(50), nullable=False, default="TECHNICAL", comment="TECHNICAL/RESEARCH/MANAGEMENT/DESIGN/DATA")
    mode: Mapped[str] = mapped_column(String(20), nullable=False, default="HYBRID", comment="REMOTE/HYBRID/ONSITE")
    stipend: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="Monthly stipend in INR")
    duration: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="e.g. '2 months', '6 months'")
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    openings: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    application_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    application_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    eligibility_criteria: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Human-readable criteria text")
    minimum_readiness_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False, comment="0-100; student's overall readiness must meet this")
    minimum_cgpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    allowed_branches: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Comma-separated branch codes, NULL=all")

    official_apply_link: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", index=True, comment="ACTIVE/CLOSED/UPCOMING")

    # Relationships
    company: Mapped["Company"] = relationship("Company", lazy="joined")
    job_role: Mapped[Optional["JobRole"]] = relationship("JobRole", lazy="joined")
    applications: Mapped[List["StudentApplication"]] = relationship(
        "StudentApplication", back_populates="internship",
        primaryjoin="StudentApplication.internship_id == Internship.id",
        lazy="select",
    )


# ─── PlacementJob ─────────────────────────────────────────────────────────────

class PlacementJob(Base, TimestampMixin):
    """
    Full-time placement job posted by a company.
    """
    __tablename__ = "placement_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    job_role_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("job_roles.id", ondelete="SET NULL"), nullable=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    package_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="LPA")
    package_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="LPA")
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bond: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="e.g. '2-year service bond'")

    eligibility_criteria: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    minimum_readiness_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    minimum_cgpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    allowed_branches: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Comma-separated branch codes, NULL=all")

    official_apply_link: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    deadline: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    openings: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", index=True)

    # Relationships
    company: Mapped["Company"] = relationship("Company", lazy="joined")
    job_role: Mapped[Optional["JobRole"]] = relationship("JobRole", lazy="joined")
    applications: Mapped[List["StudentApplication"]] = relationship(
        "StudentApplication", back_populates="placement_job",
        primaryjoin="StudentApplication.placement_job_id == PlacementJob.id",
        lazy="select",
    )


# ─── StudentApplication ───────────────────────────────────────────────────────

class StudentApplication(Base):
    """
    Tracks a student's application to an internship or placement job.
    One row per (student, internship/placement_job) pair.
    """
    __tablename__ = "student_applications"
    __table_args__ = (
        UniqueConstraint("student_id", "internship_id", name="uq_student_internship"),
        UniqueConstraint("student_id", "placement_job_id", name="uq_student_placement"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)

    internship_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("internships.id", ondelete="CASCADE"), nullable=True, index=True)
    placement_job_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("placement_jobs.id", ondelete="CASCADE"), nullable=True, index=True)

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="APPLIED", index=True)
    application_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow())
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow())
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Snapshot of readiness at time of application
    readiness_score_at_apply: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    student: Mapped["Student"] = relationship("Student", lazy="joined")
    company: Mapped["Company"] = relationship("Company", lazy="joined")
    internship: Mapped[Optional["Internship"]] = relationship(
        "Internship", back_populates="applications",
        foreign_keys=[internship_id], lazy="joined",
    )
    placement_job: Mapped[Optional["PlacementJob"]] = relationship(
        "PlacementJob", back_populates="applications",
        foreign_keys=[placement_job_id], lazy="joined",
    )
    interview_schedules: Mapped[List["InterviewSchedule"]] = relationship(
        "InterviewSchedule", back_populates="application",
        cascade="all, delete-orphan", lazy="select",
    )
    offer_letter: Mapped[Optional["OfferLetter"]] = relationship(
        "OfferLetter", back_populates="application",
        uselist=False, lazy="select",
    )


# ─── InterviewSchedule ────────────────────────────────────────────────────────

class InterviewSchedule(Base):
    """
    Scheduled interview round for a specific application.
    """
    __tablename__ = "interview_schedules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    application_id: Mapped[str] = mapped_column(String(36), ForeignKey("student_applications.id", ondelete="CASCADE"), nullable=False, index=True)
    round_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="e.g. Online Test, Technical Round 1, HR")
    scheduled_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    meeting_link: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    venue: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="SCHEDULED", comment="SCHEDULED/COMPLETED/CANCELLED/RESCHEDULED")

    # Relationship
    application: Mapped["StudentApplication"] = relationship("StudentApplication", back_populates="interview_schedules", lazy="joined")


# ─── OfferLetter ──────────────────────────────────────────────────────────────

class OfferLetter(Base):
    """
    Offer letter issued to a student upon selection.
    """
    __tablename__ = "offer_letters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("student_applications.id", ondelete="SET NULL"), nullable=True, index=True)

    offer_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="INTERNSHIP / PLACEMENT")
    package: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="LPA for placement, monthly stipend for internship")
    joining_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    offer_letter_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    accepted: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=None)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow())

    # Relationships
    student: Mapped["Student"] = relationship("Student", lazy="joined")
    company: Mapped["Company"] = relationship("Company", lazy="joined")
    application: Mapped[Optional["StudentApplication"]] = relationship("StudentApplication", back_populates="offer_letter", lazy="joined")
