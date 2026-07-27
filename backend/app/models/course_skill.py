import uuid
from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class CourseSkill(Base, TimestampMixin):
    """
    Many-to-many mapping between Courses and Skills with proficiency level.
    """
    __tablename__ = "course_skills"
    __table_args__ = (
        UniqueConstraint("course_id", "skill_id", name="uq_course_skill"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id: Mapped[str] = mapped_column(String(36), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    proficiency_level: Mapped[str] = mapped_column(
        String(50), default="BEGINNER", nullable=False,
        comment="BEGINNER, INTERMEDIATE, ADVANCED",
    )

    course: Mapped["Course"] = relationship("Course", back_populates="course_skills")
    skill: Mapped["Skill"] = relationship("Skill", back_populates="course_skills", lazy="joined")
