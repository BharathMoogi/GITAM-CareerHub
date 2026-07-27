import uuid
from typing import Optional
from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class CourseResource(Base, TimestampMixin):
    """
    Learning resource associated with a Course (video, doc, article, etc.).
    """
    __tablename__ = "course_resources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="YOUTUBE, NPTEL, DOCUMENTATION, ARTICLE, PDF, GITHUB, OFFICIAL_DOCS",
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    provider: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    duration: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="e.g. '45 mins', '2 hours'")

    course: Mapped["Course"] = relationship("Course", back_populates="resources")
