"""
Notification Engine — REST API Endpoints.

Routes:
  GET    /notifications                         → List student notifications (with filters)
  GET    /notifications/unread-count            → Count of unread notifications
  PATCH  /notifications/{notification_id}/read  → Mark single or all notifications as READ
  PATCH  /notifications/{notification_id}/archive → Archive notification
  DELETE /notifications/{notification_id}       → Delete notification
  GET    /notifications/announcements           → List campus & department announcements
  POST   /notifications/announcements           → Create campus announcement (Faculty/Placement/Admin)
  GET    /notifications/preferences            → Get user channel preferences
  PUT    /notifications/preferences            → Update notification channel preferences
  POST   /notifications/trigger                 → Trigger notification event (Event Bus API)
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.services.notification_service import NotificationService
from app.schemas.notification import (
    NotificationListResponse, AnnouncementItem, PreferenceItem,
    TriggerNotificationRequest, TriggerResponse, CreateAnnouncementRequest,
    PreferenceUpdateRequest
)
from app.core.exceptions import ForbiddenException

logger = logging.getLogger("app.api.notification")
router = APIRouter()


@router.get(
    "/notifications",
    response_model=NotificationListResponse,
    summary="List My Notifications",
    description="Returns in-app notifications for current user with filtering by status (UNREAD/READ) and category.",
)
async def get_notifications(
    status: Optional[str] = Query(None, description="Status filter: UNREAD, READ, ARCHIVED"),
    category: Optional[str] = Query(None, description="Category filter (e.g. ROADMAP_UNLOCK, PLACEMENT_DRIVE)"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    result = await service.get_user_notifications(user_id=current_user.id, status=status, category=category, limit=limit)
    return NotificationListResponse(**result)


@router.get(
    "/notifications/unread-count",
    summary="Get Unread Notification Count",
)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    count = await service.get_unread_count(user_id=current_user.id)
    return {"unread_count": count}


@router.patch(
    "/notifications/{notification_id}/read",
    summary="Mark Notification as Read",
    description="Mark a specific notification or all notifications ('all') as READ.",
)
async def mark_as_read(
    notification_id: str = Path(..., description="Notification ID or 'all'"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    return await service.mark_as_read(user_id=current_user.id, notification_id=notification_id)


@router.patch(
    "/notifications/{notification_id}/archive",
    summary="Archive Notification",
)
async def archive_notification(
    notification_id: str = Path(..., description="Notification ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    return await service.archive_notification(user_id=current_user.id, notification_id=notification_id)


@router.delete(
    "/notifications/{notification_id}",
    summary="Delete Notification",
    status_code=204,
)
async def delete_notification(
    notification_id: str = Path(..., description="Notification ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    await service.delete_notification(user_id=current_user.id, notification_id=notification_id)


@router.get(
    "/notifications/announcements",
    response_model=List[AnnouncementItem],
    summary="List Campus Announcements",
)
async def get_announcements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    results = await service.get_announcements()
    return [AnnouncementItem(**a) for a in results]


@router.post(
    "/notifications/announcements",
    response_model=AnnouncementItem,
    status_code=201,
    summary="Create Campus Announcement",
    description="Creates a campus/department wide announcement (Faculty, Placement Officer, or Admin access required).",
)
async def create_announcement(
    request: CreateAnnouncementRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in ("FACULTY", "PLACEMENT_OFFICER", "ADMIN"):
        raise ForbiddenException("Faculty, Placement Officer, or Admin access required to post announcements")

    service = NotificationService(db)
    result = await service.create_announcement(
        created_by_user_id=current_user.id,
        title=request.title,
        content=request.content,
        target_type=request.target_type,
        target_branch_id=request.target_branch_id,
        target_year=request.target_year,
        priority=request.priority,
    )
    return AnnouncementItem(**result)


@router.get(
    "/notifications/preferences",
    response_model=List[PreferenceItem],
    summary="Get Channel Preferences",
    description="Returns notification preferences per category across In-App, Email, Push, SMS, and WhatsApp channels.",
)
async def get_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    results = await service.get_preferences(user_id=current_user.id)
    return [PreferenceItem(**item) for item in results]


@router.put(
    "/notifications/preferences",
    summary="Update Channel Preferences",
)
async def update_preferences(
    request: PreferenceUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    return await service.update_preferences(
        user_id=current_user.id,
        category=request.category,
        in_app=request.in_app,
        email=request.email,
        push=request.push,
        sms=request.sms,
        whatsapp=request.whatsapp,
    )


@router.post(
    "/notifications/trigger",
    response_model=TriggerResponse,
    summary="Trigger Notification Event",
    description="Event Bus trigger endpoint for sending notifications across channels.",
)
async def trigger_notification(
    request: TriggerNotificationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    result = await service.trigger_event(
        user_id=current_user.id,
        category=request.category,
        title=request.title,
        message=request.message,
        action_url=request.action_url,
        priority=request.priority,
    )
    return TriggerResponse(**result)
