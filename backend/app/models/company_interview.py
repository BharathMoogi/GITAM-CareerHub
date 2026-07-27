import uuid
from typing import Optional
from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class CompanyInterviewRound(Base, TimestampMixin):
    """Interview round in a company's recruitment process."""
    __tablename__ = "company_interview_rounds"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    round_name: Mapped[str] = mapped_column(String(255), nullable=False)
    round_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    company: Mapped["Company"] = relationship("Company", back_populates="interview_rounds")


class CompanyInterviewQuestion(Base, TimestampMixin):
    """Interview questions asked by a company for specific job roles."""
    __tablename__ = "company_interview_questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    job_role_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("job_roles.id", ondelete="SET NULL"), nullable=True, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(50), default="MEDIUM", nullable=False, comment="EASY, MEDIUM, HARD")
    expected_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), default="TECHNICAL", nullable=False, comment="TECHNICAL, SYSTEM_DESIGN, HR, CODING, APTITUDE")

    company: Mapped["Company"] = relationship("Company", back_populates="interview_questions")
    job_role: Mapped[Optional["JobRole"]] = relationship("JobRole", lazy="joined")
