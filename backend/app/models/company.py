import uuid
from typing import Optional, List
from sqlalchemy import String, Text, Integer, Float, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class Company(Base, TimestampMixin):
    """
    Company master table representing hiring organizations.
    """
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    logo: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    industry: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    headquarters: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    company_size: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="e.g. '10,000+ employees', '1,000-5,000'")
    careers_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    glassdoor_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_hiring: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    # Relationships
    job_roles: Mapped[List["JobRole"]] = relationship("JobRole", back_populates="company", cascade="all, delete-orphan", lazy="select")
    company_skills: Mapped[List["CompanySkill"]] = relationship("CompanySkill", back_populates="company", cascade="all, delete-orphan", lazy="select")
    recommended_courses: Mapped[List["CompanyCourse"]] = relationship("CompanyCourse", back_populates="company", cascade="all, delete-orphan", lazy="select")
    recommended_projects: Mapped[List["CompanyProject"]] = relationship("CompanyProject", back_populates="company", cascade="all, delete-orphan", lazy="select")
    recommended_certifications: Mapped[List["CompanyCertification"]] = relationship("CompanyCertification", back_populates="company", cascade="all, delete-orphan", lazy="select")
    interview_rounds: Mapped[List["CompanyInterviewRound"]] = relationship("CompanyInterviewRound", back_populates="company", cascade="all, delete-orphan", order_by="CompanyInterviewRound.round_order", lazy="select")
    interview_questions: Mapped[List["CompanyInterviewQuestion"]] = relationship("CompanyInterviewQuestion", back_populates="company", cascade="all, delete-orphan", lazy="select")
