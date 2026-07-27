import uuid
from typing import Optional, List
from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class Certification(Base, TimestampMixin):
    """
    Certification master model — scoped to Branch, Year, Semester, and
    optionally linked to a RoadmapModule for auto-unlock and progress sync.
    """
    __tablename__ = "certifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    roadmap_module_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("roadmap_modules.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    provider_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        comment="NPTEL, Coursera, Cisco, AWS, Microsoft, Google, Oracle, Infosys, Intel, NVIDIA, Texas Instruments, Others",
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    official_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    difficulty: Mapped[str] = mapped_column(String(50), default="BEGINNER", nullable=False)
    estimated_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    branch_id: Mapped[str] = mapped_column(String(36), ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id: Mapped[str] = mapped_column(String(36), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)
    semester_id: Mapped[str] = mapped_column(String(36), ForeignKey("semesters.id", ondelete="CASCADE"), nullable=False, index=True)
    certificate_type: Mapped[str] = mapped_column(String(50), default="ACADEMIC", nullable=False, comment="ACADEMIC, INDUSTRY, VENDOR")
    thumbnail: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="PUBLISHED", nullable=False)

    # Relationships
    branch: Mapped["Branch"] = relationship("Branch", lazy="joined")
    academic_year: Mapped["AcademicYear"] = relationship("AcademicYear", lazy="joined")
    semester: Mapped["Semester"] = relationship("Semester", lazy="joined")
    roadmap_module: Mapped[Optional["RoadmapModule"]] = relationship("RoadmapModule", lazy="joined")

    certification_skills: Mapped[List["CertificationSkill"]] = relationship(
        "CertificationSkill", back_populates="certification", cascade="all, delete-orphan", lazy="joined"
    )
    prerequisites: Mapped[List["CertificationPrerequisite"]] = relationship(
        "CertificationPrerequisite", back_populates="certification", cascade="all, delete-orphan", lazy="joined"
    )
    exams: Mapped[List["CertificationExam"]] = relationship(
        "CertificationExam", back_populates="certification", cascade="all, delete-orphan", lazy="joined"
    )
    benefits: Mapped[List["CertificationBenefit"]] = relationship(
        "CertificationBenefit", back_populates="certification", cascade="all, delete-orphan",
        order_by="CertificationBenefit.display_order", lazy="joined"
    )
