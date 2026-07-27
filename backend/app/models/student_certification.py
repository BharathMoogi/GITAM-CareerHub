import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class StudentCertification(Base, TimestampMixin):
    """
    Tracks a student's certification status, upload/verification details,
    issue date, expiry date, and verification status.
    """
    __tablename__ = "student_certifications"
    __table_args__ = (
        UniqueConstraint("student_id", "certification_id", name="uq_student_certification"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    certification_id: Mapped[str] = mapped_column(String(36), ForeignKey("certifications.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(50), default="NOT_STARTED", nullable=False,
        comment="NOT_STARTED, IN_PROGRESS, COMPLETED",
    )

    # Verification / upload details
    certificate_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    verification_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    issue_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    student: Mapped["Student"] = relationship("Student", lazy="joined")
    certification: Mapped["Certification"] = relationship("Certification", lazy="joined")
