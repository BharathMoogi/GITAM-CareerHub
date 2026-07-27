import uuid
from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class RoadmapModuleDependency(Base, TimestampMixin):
    """
    Dependency relationship between Roadmap Modules.
    `module_id` is LOCKED until `depends_on_module_id` is COMPLETED.
    """
    __tablename__ = "roadmap_module_dependencies"
    __table_args__ = (
        UniqueConstraint("module_id", "depends_on_module_id", name="uq_module_dependency"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    module_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("roadmap_modules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    depends_on_module_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("roadmap_modules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    module: Mapped["RoadmapModule"] = relationship(
        "RoadmapModule",
        foreign_keys=[module_id],
        back_populates="prerequisite_dependencies",
    )
    depends_on_module: Mapped["RoadmapModule"] = relationship(
        "RoadmapModule",
        foreign_keys=[depends_on_module_id],
        lazy="joined",
    )
