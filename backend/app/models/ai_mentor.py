"""
AI Mentor Engine — Database Models

Tables:
  Conversation          : Chat session per student
  ConversationMessage   : Individual messages with role & token tracking
  StudentGoal           : Student's career goals
  WeeklyPlan            : AI-generated weekly study/work plans
  LearningRecommendation: AI-generated learning recommendations
"""
import uuid
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import String, Text, Integer, Float, DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class Conversation(Base):
    """A chat conversation session between a student and the AI Mentor."""
    __tablename__ = "ai_conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="New Conversation")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow())

    messages: Mapped[List["ConversationMessage"]] = relationship(
        "ConversationMessage", back_populates="conversation",
        cascade="all, delete-orphan", order_by="ConversationMessage.created_at", lazy="select",
    )
    student: Mapped["Student"] = relationship("Student", lazy="select")


class ConversationMessage(Base):
    """A single message within a conversation — either USER, ASSISTANT, or SYSTEM."""
    __tablename__ = "ai_conversation_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, comment="USER / ASSISTANT / SYSTEM")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    token_usage: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="Tokens consumed for ASSISTANT messages")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow())

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages", lazy="select")


class StudentGoal(Base):
    """
    A student-defined career goal.
    goal_type controls what kind of goal it is; goal_value stores the specific target.
    """
    __tablename__ = "student_goals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    goal_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="TARGET_COMPANY / TARGET_ROLE / HIGHER_STUDIES / RESEARCH / ENTREPRENEURSHIP"
    )
    goal_value: Mapped[str] = mapped_column(String(500), nullable=False, comment="e.g. 'Google India', 'ML Engineer'")
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", comment="ACTIVE / ACHIEVED / DROPPED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow())

    student: Mapped["Student"] = relationship("Student", lazy="select")


class WeeklyPlan(Base):
    """
    AI-generated weekly study and task plan for a student.
    tasks_json stores a JSON-encoded list of daily tasks.
    """
    __tablename__ = "ai_weekly_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    week_start: Mapped[date] = mapped_column(Date, nullable=False, comment="Monday of the plan week")
    tasks_json: Mapped[str] = mapped_column(Text, nullable=False, comment="JSON array of daily task objects")
    estimated_hours: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    completion_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow())

    student: Mapped["Student"] = relationship("Student", lazy="select")


class LearningRecommendation(Base):
    """
    AI-generated learning recommendation for a student.
    Linked to a specific item (course / project / certification / internship etc.).
    """
    __tablename__ = "ai_learning_recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    recommendation_type: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="COURSE / PROJECT / CERTIFICATION / INTERNSHIP / PLACEMENT / INTERVIEW"
    )
    item_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, comment="FK to relevant table (nullable for flexibility)")
    item_title: Mapped[str] = mapped_column(String(500), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1, comment="1=highest priority")
    reason: Mapped[str] = mapped_column(Text, nullable=False, comment="AI-generated reason for this recommendation")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow())

    student: Mapped["Student"] = relationship("Student", lazy="select")
