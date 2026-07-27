"""
Notification Engine — Database Models.

Tables:
  Notification           : In-App notifications per user
  Announcement           : Campus / Department wide broadcast announcements
  EmailQueue             : Outbound email queue with retry & schedule support
  NotificationTemplate   : Master notification & email Jinja2 templates
  NotificationPreference : User channel preferences per notification category
  NotificationDeliveryLog: Delivery audit logs across channels
"""
import uuid
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class Notification(Base):
    """In-App notifications for individual users."""
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        comment="ROADMAP_UNLOCK / COURSE_UNLOCK / PROJECT_UNLOCK / CERTIFICATE_UNLOCK / INTERVIEW_REMINDER / APPLICATION_REMINDER / PLACEMENT_DRIVE / HACKATHON / WEEKLY_AI_SUMMARY / LEADERBOARD_UPDATE / ACHIEVEMENT_EARNED",
    )
    channel: Mapped[str] = mapped_column(String(50), nullable=False, default="IN_APP", comment="IN_APP / EMAIL / PUSH / SMS / WHATSAPP")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="NORMAL", comment="LOW / NORMAL / HIGH / URGENT")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="UNREAD", comment="UNREAD / READ / ARCHIVED")
    action_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow())
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class Announcement(Base):
    """Campus or Department broadcast announcements."""
    __tablename__ = "notification_announcements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False, default="ALL", comment="ALL / BRANCH / YEAR / PLACEMENT_ELIGIBLE")
    target_branch_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("branches.id", ondelete="SET NULL"), nullable=True)
    target_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="NORMAL")
    created_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow())


class EmailQueue(Base):
    """Outbound email queue with retry logic and scheduled delivery."""
    __tablename__ = "notification_email_queue"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body_html: Mapped[str] = mapped_column(Text, nullable=False)
    template_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", comment="PENDING / SENT / FAILED / RETRY")
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow())
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class NotificationTemplate(Base):
    """Jinja2 notification and email templates."""
    __tablename__ = "notification_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    subject_template: Mapped[str] = mapped_column(String(255), nullable=False)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False, default="EMAIL")


class NotificationPreference(Base):
    """User channel preferences per notification category."""
    __tablename__ = "notification_preferences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    in_app_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sms_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    whatsapp_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "category", name="uq_user_notification_category"),)


class NotificationDeliveryLog(Base):
    """Audit log for message deliveries across all channels."""
    __tablename__ = "notification_delivery_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    notification_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="SUCCESS")
    delivered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow())
    error_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
