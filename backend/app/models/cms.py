"""
Enterprise Admin CMS — Database Models.

Tables:
  AuditLog        : System audit logging for admin actions
  ApprovalRequest : Content & entity change approval workflows
  ContentVersion  : Snapshot version history for CMS entities
  CmsBlog         : Tech & career blog posts
  CmsEvent        : Campus career events, hackathons, and webinars
  CmsResource     : Downloadable & external career resources
"""
import uuid
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class AuditLog(Base):
    """System-wide audit log recording administrative actions."""
    __tablename__ = "cms_audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, comment="CREATE / UPDATE / DELETE / RESTORE / IMPORT / EXPORT / APPROVE / REJECT")
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="STUDENT / COURSE / PROJECT / COMPANY / PLACEMENT / BLOG etc.")
    resource_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    changes_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="JSON snapshot of before/after delta")
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow(), index=True)


class ApprovalRequest(Base):
    """Approval workflow for multi-tier admin publishing."""
    __tablename__ = "cms_approval_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    requester_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    approver_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False, default="PUBLISH", comment="PUBLISH / DELETE / OVERWRITE")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", comment="PENDING / APPROVED / REJECTED")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow())
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class ContentVersion(Base):
    """Version snapshots for CMS content recovery."""
    __tablename__ = "cms_content_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow())


class CmsBlog(Base):
    """CMS Blog posts for technical and career articles."""
    __tablename__ = "cms_blogs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="CAREER_GUIDANCE")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT", comment="DRAFT / PUBLISHED / ARCHIVED")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow())


class CmsEvent(Base):
    """Campus career events, webinars, and hackathons."""
    __tablename__ = "cms_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    event_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    organizer: Mapped[str] = mapped_column(String(255), nullable=False, default="GITAM Career Cell")
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, default="WEBINAR", comment="WEBINAR / WORKSHOP / HACKATHON / DRIVE")
    registration_link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow())


class CmsResource(Base):
    """Downloadable learning and career resources."""
    __tablename__ = "cms_resources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False, default="PDF", comment="PDF / VIDEO / REPO / TEMPLATE")
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="INTERVIEW_PREP")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow())
