import uuid
from typing import Optional, List
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class AcademicYear(Base, TimestampMixin):
    """
    Academic Year Master Model (Years 1 to 4).
    """
    __tablename__ = "academic_years"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    year_number: Mapped[int] = mapped_column(
        Integer,
        unique=True,
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    semesters: Mapped[List["Semester"]] = relationship(
        "Semester",
        back_populates="academic_year",
        cascade="all, delete-orphan",
        order_by="Semester.semester_number",
    )
