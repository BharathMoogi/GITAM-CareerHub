import uuid
from typing import Optional
from sqlalchemy import String, Text, Float, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class CertificationExam(Base, TimestampMixin):
    """Exam details linked to a certification."""
    __tablename__ = "certification_exams"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    certification_id: Mapped[str] = mapped_column(String(36), ForeignKey("certifications.id", ondelete="CASCADE"), nullable=False, index=True)
    exam_name: Mapped[str] = mapped_column(String(255), nullable=False)
    exam_duration: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="e.g. '90 mins', '2 hours'")
    passing_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="Percentage or points")
    exam_pattern: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Format description, e.g. MCQs, hands-on lab")
    official_link: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    certification: Mapped["Certification"] = relationship("Certification", back_populates="exams")


class CertificationBenefit(Base, TimestampMixin):
    """Career/placement benefits of earning a certification."""
    __tablename__ = "certification_benefits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    certification_id: Mapped[str] = mapped_column(String(36), ForeignKey("certifications.id", ondelete="CASCADE"), nullable=False, index=True)
    benefit: Mapped[str] = mapped_column(Text, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    certification: Mapped["Certification"] = relationship("Certification", back_populates="benefits")
