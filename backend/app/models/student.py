import uuid
from typing import Optional
from sqlalchemy import String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class Student(Base, TimestampMixin):
    """
    Student Profile Model storing detailed academic and professional profile information.
    """
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    roll_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    phone_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    branch_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("branches.id"),
        nullable=False,
    )
    target_role_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("target_roles.id"),
        nullable=False,
    )
    current_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    semester: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    github_url: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    linkedin_url: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    leetcode_url: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    hackerrank_url: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    profile_photo: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="student_profile",
        lazy="joined",
    )
    branch: Mapped["Branch"] = relationship(
        "Branch",
        back_populates="students",
        lazy="joined",
    )
    target_role: Mapped["TargetRole"] = relationship(
        "TargetRole",
        back_populates="students",
        lazy="joined",
    )
