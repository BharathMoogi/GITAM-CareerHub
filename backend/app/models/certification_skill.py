import uuid
from typing import Optional
from sqlalchemy import String, Float, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class CertificationSkill(Base, TimestampMixin):
    """Many-to-many: Certification <-> Skill with required proficiency level."""
    __tablename__ = "certification_skills"
    __table_args__ = (
        UniqueConstraint("certification_id", "skill_id", name="uq_certification_skill"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    certification_id: Mapped[str] = mapped_column(String(36), ForeignKey("certifications.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id: Mapped[str] = mapped_column(String(36), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    required_level: Mapped[str] = mapped_column(String(50), default="BEGINNER", nullable=False)

    certification: Mapped["Certification"] = relationship("Certification", back_populates="certification_skills")
    skill: Mapped["Skill"] = relationship("Skill", lazy="joined")


class CertificationPrerequisite(Base, TimestampMixin):
    """Prerequisites required before starting a certification."""
    __tablename__ = "certification_prerequisites"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    certification_id: Mapped[str] = mapped_column(String(36), ForeignKey("certifications.id", ondelete="CASCADE"), nullable=False, index=True)
    required_course_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("courses.id", ondelete="SET NULL"), nullable=True)
    required_project_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    minimum_skill_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="0-100 score threshold")

    certification: Mapped["Certification"] = relationship("Certification", back_populates="prerequisites")
    required_course: Mapped[Optional["Course"]] = relationship("Course", lazy="joined")
    required_project: Mapped[Optional["Project"]] = relationship("Project", lazy="joined")
