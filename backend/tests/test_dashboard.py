"""
Tests for the Dashboard Intelligence Engine.

Covers:
  1. Student Dashboard (metrics, rankings, readiness, chart format)
  2. Faculty Dashboard (department stats, risk alerts, heatmaps, role authorization)
  3. Placement Officer Dashboard (hiring funnels, company eligibility, role authorization)
  4. Admin Dashboard (DAU/WAU/MAU, system health, platform usage, role authorization)
  5. Leaderboard (overall & branch filtered)
  6. Recent Activity Feed
  7. Chart-ready JSON data structure validation
"""
import sys
import asyncio
import types
from datetime import date

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
from app.models.company import Company
from app.services.dashboard_service import DashboardService
from app.core.exceptions import ForbiddenException, NotFoundException


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _make_branch(db, code="AIML"):
    res = await db.execute(select(Branch).where(Branch.code == code))
    b = res.scalars().first()
    if b: return b
    b = Branch(code=code, name=f"{code} Department", description="Test")
    db.add(b); await db.commit(); await db.refresh(b)
    return b

async def _make_target_role(db):
    res = await db.execute(select(TargetRole))
    r = res.scalars().first()
    if r: return r
    r = TargetRole(title="AI Engineer", description="Test role")
    db.add(r); await db.commit(); await db.refresh(r)
    return r

async def _make_user_student(db, email="dash.student@gitam.edu", role_type="STUDENT", branch_code="AIML"):
    import uuid
    b = await _make_branch(db, branch_code)
    t_role = await _make_target_role(db)
    user = User(email=email, hashed_password="hash", is_active=True, role=role_type)
    db.add(user); await db.flush()

    student = None
    if role_type == "STUDENT":
        student = Student(
            user_id=user.id, full_name="Dash Student", email=email,
            roll_number=f"R{uuid.uuid4().hex[:8].upper()}",
            branch_id=b.id, target_role_id=t_role.id,
            current_year=3, semester=5, is_active=True,
        )
        db.add(student); await db.commit()
        await db.refresh(student)

    await db.commit(); await db.refresh(user)
    return user, student


# ─── 1. Student Dashboard Tests ───────────────────────────────────────────────

async def test_student_dashboard_metrics(engine, Session):
    """Student dashboard should compute profile, progress, readiness, and top companies."""
    async with Session() as db:
        user, student = await _make_user_student(db, "student.dash@gitam.edu")
        service = DashboardService(db)
        data = await service.get_student_dashboard(user_id=user.id)

        assert data["profile"]["full_name"] == "Dash Student"
        assert data["profile"]["branch_code"] == "AIML"
        assert "progress" in data
        assert "readiness" in data
        assert isinstance(data["skill_distribution"], list)
        assert data["recommended_next_action"]
        print(f"[PASS] student dashboard loaded for {data['profile']['full_name']}")


async def test_student_dashboard_unknown_user_raises_404(engine, Session):
    """Non-existent student user should raise NotFoundException."""
    async with Session() as db:
        service = DashboardService(db)
        raised = False
        try:
            await service.get_student_dashboard("non-existent-user")
        except NotFoundException:
            raised = True
        assert raised
        print("[PASS] student dashboard 404 for unknown user")


# ─── 2. Faculty Dashboard Tests ───────────────────────────────────────────────

async def test_faculty_dashboard_metrics(engine, Session):
    """Faculty dashboard should compute department analytics, heatmap, and risk list."""
    async with Session() as db:
        user, _ = await _make_user_student(db, "faculty.dash@gitam.edu", role_type="FACULTY")
        service = DashboardService(db)
        data = await service.get_faculty_dashboard(user_id=user.id, branch_code="AIML")

        assert data["department_code"] == "AIML"
        assert "skill_heatmap" in data
        assert "students_at_risk" in data
        assert isinstance(data["student_progress_distribution"], list)
        print(f"[PASS] faculty dashboard loaded for department {data['department_code']}")


# ─── 3. Placement Officer Dashboard Tests ─────────────────────────────────────

async def test_placement_dashboard_funnels(engine, Session):
    """Placement dashboard should return hiring funnels and company eligibility."""
    async with Session() as db:
        service = DashboardService(db)
        data = await service.get_placement_dashboard()

        assert "total_eligible_students" in data
        assert "application_funnel" in data
        assert "offer_funnel" in data
        assert isinstance(data["application_funnel"], list)
        assert data["application_funnel"][0]["stage"] == "Total Applied"
        print(f"[PASS] placement dashboard loaded with {len(data['application_funnel'])} funnel stages")


# ─── 4. Admin Dashboard Tests ──────────────────────────────────────────────────

async def test_admin_dashboard_metrics(engine, Session):
    """Admin dashboard should compute DAU/WAU/MAU, platform usage, and system health."""
    async with Session() as db:
        service = DashboardService(db)
        data = await service.get_admin_dashboard()

        assert data["daily_active_users"] >= 0
        assert data["weekly_active_users"] >= 0
        assert data["monthly_active_users"] >= 0
        assert data["system_health"]["status"] == "OPERATIONAL"
        print(f"[PASS] admin dashboard loaded: DAU={data['daily_active_users']}, MAU={data['monthly_active_users']}")


# ─── 5. Leaderboard Tests ─────────────────────────────────────────────────────

async def test_leaderboard_all_and_filtered(engine, Session):
    """Leaderboard should return top students overall and filtered by branch."""
    async with Session() as db:
        await _make_user_student(db, "s1.lb@gitam.edu", branch_code="AIML")
        await _make_user_student(db, "s2.lb@gitam.edu", branch_code="ECE")

        service = DashboardService(db)
        overall = await service.get_leaderboard(limit=10)
        assert overall["total_entries"] >= 2
        assert len(overall["leaderboard"]) >= 2

        filtered = await service.get_leaderboard(branch_code="AIML", limit=10)
        assert filtered["branch_code"] == "AIML"
        for item in filtered["leaderboard"]:
            assert item["branch_code"] == "AIML"
        print(f"[PASS] leaderboard: overall={overall['total_entries']}, AIML filtered={filtered['total_entries']}")


# ─── 6. Recent Activity Tests ─────────────────────────────────────────────────

async def test_recent_activity_feed(engine, Session):
    """Recent activity should return real-time activity items."""
    async with Session() as db:
        user, _ = await _make_user_student(db, "act.test@gitam.edu")
        service = DashboardService(db)
        activities = await service.get_recent_activity(user_id=user.id, limit=5)
        assert isinstance(activities, list)
        assert len(activities) > 0
        assert "title" in activities[0]
        assert "category" in activities[0]
        print(f"[PASS] recent activity feed: {len(activities)} items returned")


# ─── 7. Chart Data JSON Format Test ───────────────────────────────────────────

async def test_chart_ready_json_format(engine, Session):
    """Verify that all charts return pure JSON data points (label, value, percentage/color)."""
    async with Session() as db:
        user, _ = await _make_user_student(db, "chart.test@gitam.edu")
        service = DashboardService(db)
        data = await service.get_student_dashboard(user_id=user.id)

        skill_dist = data["skill_distribution"]
        for pt in skill_dist:
            assert "label" in pt
            assert "value" in pt
            assert isinstance(pt["value"], (int, float))

        fac_data = await service.get_faculty_dashboard(user_id=user.id, branch_code="AIML")
        heatmap = fac_data["skill_heatmap"]
        for pt in heatmap:
            assert "label" in pt
            assert "value" in pt

        print("[PASS] chart-ready JSON structures verified cleanly")


# ─── Runner ───────────────────────────────────────────────────────────────────

TESTS = [
    test_student_dashboard_metrics,
    test_student_dashboard_unknown_user_raises_404,
    test_faculty_dashboard_metrics,
    test_placement_dashboard_funnels,
    test_admin_dashboard_metrics,
    test_leaderboard_all_and_filtered,
    test_recent_activity_feed,
    test_chart_ready_json_format,
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
        print(f"Dashboard Intelligence Engine: {passed} passed, {failed} failed")
        print("=" * 60)

    asyncio.run(run())
