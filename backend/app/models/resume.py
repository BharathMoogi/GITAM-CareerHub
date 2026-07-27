"""
Resume Intelligence Engine — Database Models.

Tables:
  Resume          : Primary resume profile for a student
  ResumeVersion   : Versioned snapshots (ATS JSON, PDF metadata, scores)
  Portfolio       : Portfolio configuration & personal branding
  PortfolioSection: Custom sections in personal portfolio website
  Experience      : Work / Internship experience entries
  Achievements    : Awards & honors
  Volunteer       : Volunteer / social impact work
  Publication     : Academic & conference research papers
  Patent          : Patents filed or granted
  Hackathon       : Hackathon participation & awards
"""
import uuid
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class Resume(Base, TimestampMixin):
    """Primary resume profile for a student."""
    __tablename__ = "resumes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    headline: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_role_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("target_roles.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    experiences: Mapped[List["Experience"]] = relationship("Experience", back_populates="resume", cascade="all, delete-orphan", lazy="select")
    achievements: Mapped[List["Achievements"]] = relationship("Achievements", back_populates="resume", cascade="all, delete-orphan", lazy="select")
    volunteering: Mapped[List["Volunteer"]] = relationship("Volunteer", back_populates="resume", cascade="all, delete-orphan", lazy="select")
    publications: Mapped[List["Publication"]] = relationship("Publication", back_populates="resume", cascade="all, delete-orphan", lazy="select")
    patents: Mapped[List["Patent"]] = relationship("Patent", back_populates="resume", cascade="all, delete-orphan", lazy="select")
    hackathons: Mapped[List["Hackathon"]] = relationship("Hackathon", back_populates="resume", cascade="all, delete-orphan", lazy="select")
    versions: Mapped[List["ResumeVersion"]] = relationship("ResumeVersion", back_populates="resume", cascade="all, delete-orphan", lazy="select")


class ResumeVersion(Base):
    """Versioned snapshots of generated resumes."""
    __tablename__ = "resume_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    resume_id: Mapped[str] = mapped_column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    version_name: Mapped[str] = mapped_column(String(100), nullable=False, default="v1.0")
    ats_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    resume_json: Mapped[str] = mapped_column(Text, nullable=False, comment="Full structured ATS JSON")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow())

    resume: Mapped["Resume"] = relationship("Resume", back_populates="versions", lazy="select")


class Portfolio(Base, TimestampMixin):
    """Portfolio website settings and structure."""
    __tablename__ = "portfolios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    theme: Mapped[str] = mapped_column(String(50), nullable=False, default="MODERN_DARK")
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    sections: Mapped[List["PortfolioSection"]] = relationship("PortfolioSection", back_populates="portfolio", cascade="all, delete-orphan", order_by="PortfolioSection.display_order", lazy="select")


class PortfolioSection(Base):
    """Custom section inside portfolio."""
    __tablename__ = "portfolio_sections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    portfolio_id: Mapped[str] = mapped_column(String(36), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    section_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="PROJECTS / SKILLS / CERTIFICATIONS / EXPERIENCE / ABOUT")
    content_json: Mapped[str] = mapped_column(Text, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="sections", lazy="select")


class Experience(Base):
    """Internship or work experience entry."""
    __tablename__ = "resume_experiences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    resume_id: Mapped[str] = mapped_column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role_title: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    bullet_points_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]", comment="JSON list of bullet strings")

    resume: Mapped["Resume"] = relationship("Resume", back_populates="experiences", lazy="select")


class Achievements(Base):
    """Academic or extracurricular awards/honors."""
    __tablename__ = "resume_achievements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    resume_id: Mapped[str] = mapped_column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    issuer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    date_awarded: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    resume: Mapped["Resume"] = relationship("Resume", back_populates="achievements", lazy="select")


class Volunteer(Base):
    """Volunteering / community leadership entries."""
    __tablename__ = "resume_volunteers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    resume_id: Mapped[str] = mapped_column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    organization: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    resume: Mapped["Resume"] = relationship("Resume", back_populates="volunteering", lazy="select")


class Publication(Base):
    """Research publications."""
    __tablename__ = "resume_publications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    resume_id: Mapped[str] = mapped_column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    journal_publisher: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    publication_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    paper_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    authors: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    resume: Mapped["Resume"] = relationship("Resume", back_populates="publications", lazy="select")


class Patent(Base):
    """Patents filed or granted."""
    __tablename__ = "resume_patents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    resume_id: Mapped[str] = mapped_column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    patent_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    filing_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="FILED", comment="FILED / GRANTED / PENDING")
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    resume: Mapped["Resume"] = relationship("Resume", back_populates="patents", lazy="select")


class Hackathon(Base):
    """Hackathon wins & participation."""
    __tablename__ = "resume_hackathons"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    resume_id: Mapped[str] = mapped_column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    event_name: Mapped[str] = mapped_column(String(255), nullable=False)
    project_title: Mapped[str] = mapped_column(String(255), nullable=False)
    prize_rank: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="e.g. '1st Place', 'Finalist'")
    date_held: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    repo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    resume: Mapped["Resume"] = relationship("Resume", back_populates="hackathons", lazy="select")
