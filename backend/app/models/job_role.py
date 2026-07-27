import uuid
from typing import Optional
from sqlalchemy import String, Text, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class JobRole(Base, TimestampMixin):
    """
    JobRole offered by a Company.
    """
    __tablename__ = "job_roles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    role_category: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="e.g. 'Embedded', 'AI/ML', 'VLSI', 'Software', 'Mechanical', 'Electrical'")
    employment_type: Mapped[str] = mapped_column(String(50), default="FULL_TIME", nullable=False, comment="FULL_TIME, INTERNSHIP, TRAINEE")
    experience_level: Mapped[str] = mapped_column(String(50), default="ENTRY_LEVEL", nullable=False, comment="ENTRY_LEVEL, MID_LEVEL, SENIOR")
    salary_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="LPA or annual salary min")
    salary_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="LPA or annual salary max")
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    job_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)

    company: Mapped["Company"] = relationship("Company", back_populates="job_roles")
