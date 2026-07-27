"""
Pydantic schemas for Notification Engine API.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── Requests ──────────────────────────────────────────────────────────────────

class TriggerNotificationRequest(BaseModel):
    category: str = Field(..., description="One of: ROADMAP_UNLOCK, COURSE_UNLOCK, PROJECT_UNLOCK, CERTIFICATE_UNLOCK, INTERVIEW_REMINDER, APPLICATION_REMINDER, PLACEMENT_DRIVE, HACKATHON, WEEKLY_AI_SUMMARY, LEADERBOARD_UPDATE, ACHIEVEMENT_EARNED")
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1, max_length=2000)
    action_url: Optional[str] = None
    priority: str = Field(default="NORMAL", description="LOW / NORMAL / HIGH / URGENT")


class CreateAnnouncementRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1, max_length=4000)
    target_type: str = Field(default="ALL", description="ALL / BRANCH / YEAR / PLACEMENT_ELIGIBLE")
    target_branch_id: Optional[str] = None
    target_year: Optional[int] = None
    priority: str = Field(default="NORMAL")


class PreferenceUpdateRequest(BaseModel):
    category: str
    in_app: bool = True
    email: bool = True
    push: bool = True
    sms: bool = False
    whatsapp: bool = False


# ── Responses ─────────────────────────────────────────────────────────────────

class NotificationItem(BaseModel):
    id: str
    title: str
    message: str
    category: str
    channel: str
    priority: str
    status: str
    action_url: Optional[str] = None
    created_at: str
    read_at: Optional[str] = None


class NotificationListResponse(BaseModel):
    unread_count: int
    total: int
    notifications: List[NotificationItem]


class AnnouncementItem(BaseModel):
    id: str
    title: str
    content: str
    target_type: str
    priority: str
    created_at: str


class PreferenceItem(BaseModel):
    category: str
    in_app_enabled: bool
    email_enabled: bool
    push_enabled: bool
    sms_enabled: bool
    whatsapp_enabled: bool


class TriggerResponse(BaseModel):
    notification_id: str
    email_queue_id: str
    status: str
    channels: List[str]
