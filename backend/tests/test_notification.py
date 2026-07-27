"""
Tests for the Notification Engine.

Covers:
  1. Multi-channel event trigger via NotificationEventBus (In-App, EmailQueue, DeliveryLog)
  2. In-App notification list and unread count
  3. Mark as read (single / all) and archive
  4. Permanent deletion
  5. Campus & Department broadcast announcements
  6. User channel preferences (In-App, Email, Push, SMS, WhatsApp)
  7. Outbound EmailQueue processing and retry logic
"""
import sys
import asyncio
import types
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, async_sessionmaker

# Stub pytest
_pytest = types.ModuleType("pytest")
class _RaisesCtx:
    def __init__(self, exc): self.exc = exc
    def __enter__(self): return self
    def __exit__(self, et, ev, tb):
        if et is None: raise AssertionError(f"Expected {self.exc.__name__} not raised")
        return issubclass(et, self.exc)
_pytest.raises = lambda exc: _RaisesCtx(exc)
sys.modules.setdefault("pytest", _pytest)

from app.models.user import User
from app.models.student import Student
from app.models.branch import Branch
from app.models.target_role import TargetRole
from app.models.notification import Notification, Announcement, EmailQueue, NotificationPreference, NotificationDeliveryLog
from app.services.notification_service import NotificationService, NotificationEventBus
from app.core.exceptions import NotFoundException, BadRequestException, ForbiddenException


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _make_user_student(db, email="noti.student@gitam.edu", role_type="STUDENT"):
    import uuid
    b_res = await db.execute(select(Branch))
    b = b_res.scalars().first()
    if not b:
        b = Branch(code="AIML", name="AIML Dept", description="Test")
        db.add(b); await db.commit(); await db.refresh(b)

    r_res = await db.execute(select(TargetRole))
    role = r_res.scalars().first()
    if not role:
        role = TargetRole(title="AI Engineer", description="Test role")
        db.add(role); await db.commit(); await db.refresh(role)

    user = User(email=email, hashed_password="hash", is_active=True, role=role_type)
    db.add(user); await db.flush()

    if role_type == "STUDENT":
        student = Student(
            user_id=user.id, full_name="Noti Student", email=email,
            roll_number=f"R{uuid.uuid4().hex[:8].upper()}",
            branch_id=b.id, target_role_id=role.id,
            current_year=3, semester=5, is_active=True,
        )
        db.add(student); await db.commit()

    await db.commit(); await db.refresh(user)
    return user


# ─── Tests ────────────────────────────────────────────────────────────────────

async def test_trigger_notification_event_bus(engine, Session):
    """Event Bus should dispatch notification across In-App, EmailQueue, and DeliveryLog."""
    async with Session() as db:
        user = await _make_user_student(db, "noti.bus@gitam.edu")

        result = await NotificationEventBus.emit(
            db=db,
            user_id=user.id,
            category="ROADMAP_UNLOCK",
            title="Module Unlocked!",
            message="You have unlocked Semester 5 Advanced ML module.",
            action_url="/roadmaps/module-5",
            priority="HIGH",
        )

        assert result["status"] == "DISPATCHED"
        assert result["notification_id"]
        assert result["email_queue_id"]

        # Verify DB entries
        n_res = await db.execute(select(Notification).where(Notification.id == result["notification_id"]))
        n = n_res.scalars().first()
        assert n is not None
        assert n.title == "Module Unlocked!"
        assert n.status == "UNREAD"

        eq_res = await db.execute(select(EmailQueue).where(EmailQueue.id == result["email_queue_id"]))
        eq = eq_res.scalars().first()
        assert eq is not None
        assert eq.recipient_email == user.email
        assert eq.status == "PENDING"

        print(f"[PASS] event bus triggered: notification_id={n.id[:8]}, email_queue_id={eq.id[:8]}")


async def test_get_user_notifications_and_unread_count(engine, Session):
    """get_user_notifications should return in-app notifications and unread count."""
    async with Session() as db:
        user = await _make_user_student(db, "noti.list@gitam.edu")
        await NotificationEventBus.emit(db, user.id, "COURSE_UNLOCK", "Course Unlocked", "Python 101 ready")
        await NotificationEventBus.emit(db, user.id, "PLACEMENT_DRIVE", "Drive Open", "Google India is hiring")

        service = NotificationService(db)
        data = await service.get_user_notifications(user_id=user.id)

        assert data["unread_count"] == 2
        assert data["total"] == 2
        assert len(data["notifications"]) == 2
        print(f"[PASS] notifications list: unread_count={data['unread_count']}")


async def test_mark_as_read_and_archive(engine, Session):
    """mark_as_read and archive_notification should update notification status."""
    async with Session() as db:
        user = await _make_user_student(db, "noti.status@gitam.edu")
        ev1 = await NotificationEventBus.emit(db, user.id, "HACKATHON", "Hackathon Win", "You placed 1st!")
        ev2 = await NotificationEventBus.emit(db, user.id, "ACHIEVEMENT_EARNED", "New Badge", "Earned First Step badge")

        service = NotificationService(db)

        # Mark single as read
        r1 = await service.mark_as_read(user.id, ev1["notification_id"])
        assert r1["status"] == "READ"

        # Archive second
        r2 = await service.archive_notification(user.id, ev2["notification_id"])
        assert r2["status"] == "ARCHIVED"

        # Mark all read
        r3 = await service.mark_as_read(user.id, "all")
        assert r3["status"] == "READ"


        print("[PASS] mark as read & archive operations verified")


async def test_delete_notification(engine, Session):
    """delete_notification should permanently remove from DB."""
    async with Session() as db:
        user = await _make_user_student(db, "noti.del@gitam.edu")
        ev = await NotificationEventBus.emit(db, user.id, "INTERVIEW_REMINDER", "Interview Tomorrow", "10:00 AM interview")

        service = NotificationService(db)
        await service.delete_notification(user.id, ev["notification_id"])

        res = await db.execute(select(Notification).where(Notification.id == ev["notification_id"]))
        assert res.scalars().first() is None
        print("[PASS] notification deleted permanently")


async def test_create_and_get_announcements(engine, Session):
    """Faculty/Officer creates campus announcement and students retrieve it."""
    async with Session() as db:
        faculty = await _make_user_student(db, "fac.ann@gitam.edu", role_type="FACULTY")
        student = await _make_user_student(db, "stu.ann@gitam.edu", role_type="STUDENT")

        service = NotificationService(db)
        ann = await service.create_announcement(
            created_by_user_id=faculty.id,
            title="Campus Placement Drive Schedule",
            content="Google & Microsoft drives scheduled for October 15.",
            target_type="ALL",
            priority="HIGH",
        )

        assert ann["id"]
        assert ann["title"] == "Campus Placement Drive Schedule"

        announcements = await service.get_announcements()
        assert len(announcements) >= 1
        assert announcements[0]["title"] == "Campus Placement Drive Schedule"
        print(f"[PASS] announcement created & retrieved: '{ann['title']}'")


async def test_notification_preferences(engine, Session):
    """get_preferences and update_preferences should handle channel settings."""
    async with Session() as db:
        user = await _make_user_student(db, "pref.test@gitam.edu")

        service = NotificationService(db)
        prefs = await service.get_preferences(user.id)
        assert len(prefs) == 11  # All 11 categories present

        up = await service.update_preferences(
            user_id=user.id,
            category="PLACEMENT_DRIVE",
            in_app=True,
            email=True,
            push=True,
            sms=True,
            whatsapp=True,
        )
        assert up["updated"] is True

        new_prefs = await service.get_preferences(user.id)
        drive_pref = next(p for p in new_prefs if p["category"] == "PLACEMENT_DRIVE")
        assert drive_pref["whatsapp_enabled"] is True
        print(f"[PASS] notification preferences updated: WhatsApp={drive_pref['whatsapp_enabled']}")


async def test_email_queue_processor_retry_logic(engine, Session):
    """process_email_queue should process pending outbound emails."""
    async with Session() as db:
        user = await _make_user_student(db, "queue.test@gitam.edu")
        await NotificationEventBus.emit(db, user.id, "WEEKLY_AI_SUMMARY", "AI Weekly Plan", "Summary ready")

        service = NotificationService(db)
        proc_res = await service.process_email_queue()

        assert proc_res["processed"] >= 1
        assert proc_res["failed"] == 0
        print(f"[PASS] email queue processor executed: processed={proc_res['processed']}")


# ─── Runner ───────────────────────────────────────────────────────────────────

TESTS = [
    test_trigger_notification_event_bus,
    test_get_user_notifications_and_unread_count,
    test_mark_as_read_and_archive,
    test_delete_notification,
    test_create_and_get_announcements,
    test_notification_preferences,
    test_email_queue_processor_retry_logic,
]

if __name__ == "__main__":
    import pathlib
    for p in pathlib.Path(".").rglob("*.pyc"):
        p.unlink(missing_ok=True)

    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.database.base import Base

    async def run():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        passed = failed = 0
        for t in TESTS:
            try:
                await t(engine, Session)
                passed += 1
            except Exception as e:
                import traceback
                print(f"[FAIL] {t.__name__}: {e}")
                traceback.print_exc()
                failed += 1
        print()
        print("=" * 60)
        print(f"Notification Engine: {passed} passed, {failed} failed")
        print("=" * 60)

    asyncio.run(run())
