import uuid
from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class ProjectSkill(Base, TimestampMixin):
    """Many-to-many: Project <-> Skill with required proficiency level."""
    __tablename__ = "project_skills"
    __table_args__ = (
        UniqueConstraint("project_id", "skill_id", name="uq_project_skill"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id: Mapped[str] = mapped_column(String(36), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    required_level: Mapped[str] = mapped_column(String(50), default="BEGINNER", nullable=False, comment="BEGINNER, INTERMEDIATE, ADVANCED")

    project: Mapped["Project"] = relationship("Project", back_populates="project_skills")
    skill: Mapped["Skill"] = relationship("Skill", lazy="joined")


class ProjectTechnologyMap(Base, TimestampMixin):
    """Many-to-many: Project <-> ProjectTechnology."""
    __tablename__ = "project_technology_maps"
    __table_args__ = (
        UniqueConstraint("project_id", "technology_id", name="uq_project_technology"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    technology_id: Mapped[str] = mapped_column(String(36), ForeignKey("project_technologies.id", ondelete="CASCADE"), nullable=False, index=True)

    project: Mapped["Project"] = relationship("Project", back_populates="technology_maps")
    technology: Mapped["ProjectTechnology"] = relationship("ProjectTechnology", back_populates="technology_maps", lazy="joined")
