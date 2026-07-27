import uuid
from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class RoadmapModule(Base, TimestampMixin):
    """
    Roadmap Module Model representing individual learning/academic units.
    """
    __tablename__ = "roadmap_modules"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    roadmap_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("roadmaps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    module_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    module_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="COURSE, QUIZ, PROJECT, CERTIFICATION, SKILL, INTERNSHIP, PLACEMENT, AI_LEARNING, PROFILE_SETUP",
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    is_required: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    estimated_hours: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
    )

    # Relationships
    roadmap: Mapped["Roadmap"] = relationship("Roadmap", back_populates="modules")
    
    # Prerequisite dependencies required before unlocking THIS module
    prerequisite_dependencies: Mapped[List["RoadmapModuleDependency"]] = relationship(
        "RoadmapModuleDependency",
        foreign_keys="RoadmapModuleDependency.module_id",
        back_populates="module",
        cascade="all, delete-orphan",
        lazy="joined",
    )
