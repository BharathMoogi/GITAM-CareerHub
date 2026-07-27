import uuid
from typing import Optional, List
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class Semester(Base, TimestampMixin):
    """
    Semester Master Model (Semesters 1 to 8).
    """
    __tablename__ = "semesters"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    academic_year_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    semester_number: Mapped[int] = mapped_column(
        Integer,
        unique=True,
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    academic_year: Mapped["AcademicYear"] = relationship(
        "AcademicYear",
        back_populates="semesters",
        lazy="joined",
    )
