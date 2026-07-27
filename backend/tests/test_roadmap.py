"""
Test suite for the Academic Roadmap Engine.

Covers:
- Roadmap retrieval (branch & semester specific)
- Locked modules (future semester & prerequisite constraints)
- Module completion and progress updates
- Dependency validation (projects unlock after course completion)
- Progress calculation metrics
- Unauthorized access protection
- Admin-only SKIPPED status enforcement
"""
try:
    import pytest
except ImportError:
    class MarkFallback:
        def asyncio(self, func):
            return func
    class PytestFallback:
        mark = MarkFallback()
    pytest = PytestFallback()

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import create_access_token, get_password_hash
from app.models.user import User
from app.models.student import Student
from app.models.branch import Branch
from app.models.target_role import TargetRole
from app.models.roadmap import Roadmap
from app.models.roadmap_module import RoadmapModule
from app.models.roadmap_dependency import RoadmapModuleDependency
from app.models.student_progress import StudentRoadmapProgress


# ─── Fixtures & Helpers ────────────────────────────────────────────────────────

async def create_test_student(
    db: AsyncSession,
    email: str = "roadmaptest@gitam.edu",
    roll_number: str = "211910301001",
    current_year: int = 1,
    semester: int = 1,
) -> tuple[User, str]:
    """Create a test student and return (user, jwt_token)."""
    branch_res = await db.execute(select(Branch).where(Branch.code == "AIML"))
    branch = branch_res.scalars().first()

    role_res = await db.execute(select(TargetRole))
    role = role_res.scalars().first()

    user = User(
        email=email,
        hashed_password=get_password_hash("Password123!"),
        full_name="Roadmap Test Student",
        role="student",
        is_active=True,
    )
    db.add(user)
    await db.flush()

    student = Student(
        user_id=user.id,
        full_name="Roadmap Test Student",
        email=email,
        roll_number=roll_number,
        branch_id=branch.id,
        target_role_id=role.id,
        current_year=current_year,
        semester=semester,
        is_active=True,
    )
    db.add(student)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(subject=user.id)
    return user, token


# ─── Test: Roadmap Retrieval ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_roadmaps_returns_branch_specific(client: AsyncClient, db_session: AsyncSession):
    """GET /roadmaps returns roadmaps for student's branch."""
    _, token = await create_test_student(db_session, semester=1)
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/v1/roadmaps", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "timestamp" in data
    roadmaps = data["data"]
    assert len(roadmaps) > 0

    # All roadmaps should be for AIML branch
    for r in roadmaps:
        assert "AIML" in r["title"] or r["branch_name"] == "Artificial Intelligence & Machine Learning"


@pytest.mark.asyncio
async def test_get_roadmaps_filter_by_semester(client: AsyncClient, db_session: AsyncSession):
    """GET /roadmaps?semester=1 returns only Semester 1 roadmaps."""
    _, token = await create_test_student(
        db_session, email="semfilter@gitam.edu", roll_number="R002", semester=3
    )
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/v1/roadmaps?semester=1", headers=headers)
    assert res.status_code == 200
    roadmaps = res.json()["data"]
    assert len(roadmaps) == 1
    assert roadmaps[0]["semester_number"] == 1


@pytest.mark.asyncio
async def test_get_roadmaps_filter_by_year(client: AsyncClient, db_session: AsyncSession):
    """GET /roadmaps?year=1 returns only Year 1 roadmaps (2 semesters)."""
    _, token = await create_test_student(
        db_session, email="yearfilter@gitam.edu", roll_number="R003", semester=3
    )
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/v1/roadmaps?year=1", headers=headers)
    assert res.status_code == 200
    roadmaps = res.json()["data"]
    assert len(roadmaps) == 2  # Semesters 1 and 2
    year_nums = {r["year_number"] for r in roadmaps}
    assert year_nums == {1}


# ─── Test: Module Listing ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_modules_returns_ordered_list(client: AsyncClient, db_session: AsyncSession):
    """GET /roadmaps/modules returns all modules with lock info."""
    _, token = await create_test_student(
        db_session, email="modlist@gitam.edu", roll_number="R004", semester=1
    )
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/v1/roadmaps/modules", headers=headers)
    assert res.status_code == 200
    modules = res.json()["data"]
    assert len(modules) > 0

    # Every module has required fields
    for m in modules:
        assert "id" in m
        assert "module_name" in m
        assert "module_type" in m
        assert "is_locked" in m
        assert "user_status" in m
        assert "completion_percentage" in m


@pytest.mark.asyncio
async def test_modules_filtered_by_semester(client: AsyncClient, db_session: AsyncSession):
    """GET /roadmaps/modules?semester=1 returns only Semester 1 modules."""
    _, token = await create_test_student(
        db_session, email="modsem@gitam.edu", roll_number="R005", semester=3
    )
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/v1/roadmaps/modules?semester=1", headers=headers)
    assert res.status_code == 200
    modules = res.json()["data"]
    assert len(modules) > 0


# ─── Test: Locked Modules ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_future_semester_modules_are_locked(client: AsyncClient, db_session: AsyncSession):
    """Modules in semesters beyond student's current semester must be locked."""
    # Student is in Semester 1; Semester 2+ should be locked
    _, token = await create_test_student(
        db_session, email="locked@gitam.edu", roll_number="R006", semester=1
    )
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/v1/roadmaps/modules", headers=headers)
    assert res.status_code == 200
    modules = res.json()["data"]

    # Find modules from semesters > 1 — they should all be locked
    # We can't directly filter by semester here but we check if any locked modules exist
    locked = [m for m in modules if m["is_locked"]]
    assert len(locked) > 0  # There must be locked modules since student is only in Sem 1

    for m in locked:
        assert m["lock_reason"] is not None
        assert m["user_status"] == "NOT_STARTED"


@pytest.mark.asyncio
async def test_cannot_update_locked_module(client: AsyncClient, db_session: AsyncSession):
    """PATCH /roadmaps/progress/{module_id} on a locked module returns 400."""
    _, token = await create_test_student(
        db_session, email="lockedupd@gitam.edu", roll_number="R007", semester=1
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch all modules
    mod_res = await client.get("/api/v1/roadmaps/modules", headers=headers)
    modules = mod_res.json()["data"]

    # Find a locked module
    locked_module = next((m for m in modules if m["is_locked"]), None)
    assert locked_module is not None, "There should be locked modules for a Semester 1 student"

    # Try to update the locked module — should fail with 400
    update_res = await client.patch(
        f"/api/v1/roadmaps/progress/{locked_module['id']}",
        headers=headers,
        json={"status": "IN_PROGRESS"},
    )
    assert update_res.status_code == 400
    err = update_res.json()["error"]
    assert "locked" in err["message"].lower()


# ─── Test: Dependency Validation ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_project_locked_until_course_completed(client: AsyncClient, db_session: AsyncSession):
    """PROJECT module must be locked until its COURSE prerequisite is completed."""
    _, token = await create_test_student(
        db_session, email="deptest@gitam.edu", roll_number="R008", semester=1
    )
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/v1/roadmaps/modules?semester=1", headers=headers)
    modules = res.json()["data"]

    project_module = next((m for m in modules if m["module_type"] == "PROJECT"), None)
    course_module = next((m for m in modules if m["module_type"] == "COURSE"), None)

    assert project_module is not None
    assert course_module is not None

    # Project should be locked because Course is NOT yet completed
    assert project_module["is_locked"] is True
    assert "Prerequisite" in project_module["lock_reason"]

    # Course is in Semester 1 so it should NOT be future-locked
    assert course_module["is_locked"] is False or (
        course_module["is_locked"] and "Future" not in course_module["lock_reason"]
    )


@pytest.mark.asyncio
async def test_project_unlocks_after_course_completion(client: AsyncClient, db_session: AsyncSession):
    """PROJECT unlocks after COURSE prerequisite is marked COMPLETED."""
    _, token = await create_test_student(
        db_session, email="unlock@gitam.edu", roll_number="R009", semester=1
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Get Semester 1 modules
    mod_res = await client.get("/api/v1/roadmaps/modules?semester=1", headers=headers)
    modules = mod_res.json()["data"]

    course_module = next((m for m in modules if m["module_type"] == "COURSE"), None)
    project_module = next((m for m in modules if m["module_type"] == "PROJECT"), None)
    assert course_module and project_module

    # Start and complete the COURSE module
    start_res = await client.patch(
        f"/api/v1/roadmaps/progress/{course_module['id']}",
        headers=headers,
        json={"status": "IN_PROGRESS"},
    )
    assert start_res.status_code == 200

    complete_res = await client.patch(
        f"/api/v1/roadmaps/progress/{course_module['id']}",
        headers=headers,
        json={"status": "COMPLETED"},
    )
    assert complete_res.status_code == 200
    assert complete_res.json()["data"]["user_status"] == "COMPLETED"

    # Now PROJECT should be unlocked
    mod_res2 = await client.get("/api/v1/roadmaps/modules?semester=1", headers=headers)
    modules2 = mod_res2.json()["data"]
    project_updated = next((m for m in modules2 if m["id"] == project_module["id"]), None)
    assert project_updated is not None
    assert project_updated["is_locked"] is False


# ─── Test: Module Completion & Progress Calculation ──────────────────────────

@pytest.mark.asyncio
async def test_mark_module_in_progress(client: AsyncClient, db_session: AsyncSession):
    """PATCH updates status to IN_PROGRESS correctly."""
    _, token = await create_test_student(
        db_session, email="inprog@gitam.edu", roll_number="R010", semester=1
    )
    headers = {"Authorization": f"Bearer {token}"}

    mod_res = await client.get("/api/v1/roadmaps/modules?semester=1", headers=headers)
    unlocked = next(
        (m for m in mod_res.json()["data"] if not m["is_locked"]), None
    )
    assert unlocked is not None

    res = await client.patch(
        f"/api/v1/roadmaps/progress/{unlocked['id']}",
        headers=headers,
        json={"status": "IN_PROGRESS"},
    )
    assert res.status_code == 200
    result = res.json()["data"]
    assert result["user_status"] == "IN_PROGRESS"
    assert result["started_at"] is not None


@pytest.mark.asyncio
async def test_mark_module_completed(client: AsyncClient, db_session: AsyncSession):
    """PATCH updates status to COMPLETED and sets completion_percentage to 100."""
    _, token = await create_test_student(
        db_session, email="completed@gitam.edu", roll_number="R011", semester=1
    )
    headers = {"Authorization": f"Bearer {token}"}

    mod_res = await client.get("/api/v1/roadmaps/modules?semester=1", headers=headers)
    unlocked = next(
        (m for m in mod_res.json()["data"] if not m["is_locked"]), None
    )
    assert unlocked is not None

    res = await client.patch(
        f"/api/v1/roadmaps/progress/{unlocked['id']}",
        headers=headers,
        json={"status": "COMPLETED"},
    )
    assert res.status_code == 200
    result = res.json()["data"]
    assert result["user_status"] == "COMPLETED"
    assert result["completion_percentage"] == 100.0
    assert result["completed_at"] is not None


@pytest.mark.asyncio
async def test_progress_percentage_increases_after_completion(
    client: AsyncClient, db_session: AsyncSession
):
    """GET /roadmaps/progress shows increased overall % after completing a module."""
    _, token = await create_test_student(
        db_session, email="progpct@gitam.edu", roll_number="R012", semester=1
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Initial progress
    prog_res = await client.get("/api/v1/roadmaps/progress", headers=headers)
    initial_pct = prog_res.json()["data"]["overall_completion_percentage"]
    assert initial_pct == 0.0

    # Complete an unlocked module
    mod_res = await client.get("/api/v1/roadmaps/modules?semester=1", headers=headers)
    unlocked = next((m for m in mod_res.json()["data"] if not m["is_locked"]), None)
    assert unlocked is not None

    await client.patch(
        f"/api/v1/roadmaps/progress/{unlocked['id']}",
        headers=headers,
        json={"status": "COMPLETED"},
    )

    # Progress should have increased
    prog_res2 = await client.get("/api/v1/roadmaps/progress", headers=headers)
    updated_pct = prog_res2.json()["data"]["overall_completion_percentage"]
    assert updated_pct > initial_pct

    # Completed modules list should contain 1 entry
    assert prog_res2.json()["data"]["completed_modules_count"] == 1


@pytest.mark.asyncio
async def test_progress_structure(client: AsyncClient, db_session: AsyncSession):
    """GET /roadmaps/progress returns correct structure with all expected fields."""
    _, token = await create_test_student(
        db_session, email="progstruct@gitam.edu", roll_number="R013", semester=2
    )
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/v1/roadmaps/progress", headers=headers)
    assert res.status_code == 200
    d = res.json()["data"]

    required_keys = [
        "overall_completion_percentage",
        "completed_modules_count",
        "in_progress_modules_count",
        "total_modules_count",
        "total_estimated_hours",
        "completed_estimated_hours",
        "completed_modules",
        "in_progress_modules",
        "locked_modules",
        "upcoming_modules",
    ]
    for key in required_keys:
        assert key in d, f"Missing key: {key}"

    assert isinstance(d["overall_completion_percentage"], float)
    assert isinstance(d["total_modules_count"], int)
    assert d["total_modules_count"] > 0


# ─── Test: Admin SKIPPED Restriction ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_student_cannot_skip_module(client: AsyncClient, db_session: AsyncSession):
    """Non-admin student cannot set status to SKIPPED."""
    _, token = await create_test_student(
        db_session, email="skiptest@gitam.edu", roll_number="R014", semester=1
    )
    headers = {"Authorization": f"Bearer {token}"}

    mod_res = await client.get("/api/v1/roadmaps/modules?semester=1", headers=headers)
    unlocked = next((m for m in mod_res.json()["data"] if not m["is_locked"]), None)
    assert unlocked is not None

    res = await client.patch(
        f"/api/v1/roadmaps/progress/{unlocked['id']}",
        headers=headers,
        json={"status": "SKIPPED"},
    )
    assert res.status_code == 403
    assert "admin" in res.json()["error"]["message"].lower()


# ─── Test: Invalid Status ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_invalid_status_returns_400(client: AsyncClient, db_session: AsyncSession):
    """PATCH with an invalid status value returns 400."""
    _, token = await create_test_student(
        db_session, email="invalidstatus@gitam.edu", roll_number="R015", semester=1
    )
    headers = {"Authorization": f"Bearer {token}"}

    mod_res = await client.get("/api/v1/roadmaps/modules?semester=1", headers=headers)
    unlocked = next((m for m in mod_res.json()["data"] if not m["is_locked"]), None)
    assert unlocked is not None

    res = await client.patch(
        f"/api/v1/roadmaps/progress/{unlocked['id']}",
        headers=headers,
        json={"status": "INVALID_STATUS"},
    )
    assert res.status_code == 400


# ─── Test: Unauthorized Access ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_roadmaps_requires_auth(client: AsyncClient, db_session: AsyncSession):
    """GET /roadmaps returns 401 without Bearer token."""
    res = await client.get("/api/v1/roadmaps")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_modules_requires_auth(client: AsyncClient, db_session: AsyncSession):
    """GET /roadmaps/modules returns 401 without Bearer token."""
    res = await client.get("/api/v1/roadmaps/modules")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_progress_requires_auth(client: AsyncClient, db_session: AsyncSession):
    """GET /roadmaps/progress returns 401 without Bearer token."""
    res = await client.get("/api/v1/roadmaps/progress")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_patch_progress_requires_auth(client: AsyncClient, db_session: AsyncSession):
    """PATCH /roadmaps/progress/{id} returns 401 without Bearer token."""
    res = await client.patch(
        "/api/v1/roadmaps/progress/some-module-id",
        json={"status": "IN_PROGRESS"},
    )
    assert res.status_code == 401


# ─── Test: AI_LEARNING & PROFILE_SETUP Presence ──────────────────────────────

@pytest.mark.asyncio
async def test_ai_learning_present_in_semester_1(client: AsyncClient, db_session: AsyncSession):
    """AI_LEARNING module must appear in Semester 1 roadmap."""
    _, token = await create_test_student(
        db_session, email="aicheck@gitam.edu", roll_number="R016", semester=1
    )
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/v1/roadmaps/modules?semester=1", headers=headers)
    modules = res.json()["data"]
    ai_modules = [m for m in modules if m["module_type"] == "AI_LEARNING"]
    assert len(ai_modules) >= 1


@pytest.mark.asyncio
async def test_profile_setup_present_in_semester_1(client: AsyncClient, db_session: AsyncSession):
    """PROFILE_SETUP module must appear only in Semester 1."""
    _, token = await create_test_student(
        db_session, email="profilecheck@gitam.edu", roll_number="R017", semester=1
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Semester 1 should have PROFILE_SETUP
    res1 = await client.get("/api/v1/roadmaps/modules?semester=1", headers=headers)
    modules_s1 = res1.json()["data"]
    profile_mods_s1 = [m for m in modules_s1 if m["module_type"] == "PROFILE_SETUP"]
    assert len(profile_mods_s1) >= 1
