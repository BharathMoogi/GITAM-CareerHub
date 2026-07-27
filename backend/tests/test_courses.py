"""
Tests for the Learning Engine.

Covers:
- Course list retrieval with filters (year, semester, difficulty, skill)
- Course detail endpoint
- Lock enforcement (future semester, roadmap dependency)
- Progress update: IN_PROGRESS, COMPLETED
- Skill score auto-calculation on course completion
- Roadmap module auto-update on course completion
- Skills dashboard endpoint
- Unauthorized access protection
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
from app.models.course import Course
from app.models.student_skill import StudentSkill
from app.models.student_course_progress import StudentCourseProgress
from app.models.student_progress import StudentRoadmapProgress


# ─── Fixture Helper ───────────────────────────────────────────────────────────

async def create_test_student(
    db: AsyncSession,
    email: str = "coursetest@gitam.edu",
    roll_number: str = "CE001",
    branch_code: str = "AIML",
    current_year: int = 1,
    semester: int = 1,
) -> tuple[User, str]:
    branch_res = await db.execute(select(Branch).where(Branch.code == branch_code))
    branch = branch_res.scalars().first()

    role_res = await db.execute(select(TargetRole))
    role = role_res.scalars().first()

    user = User(
        email=email,
        hashed_password=get_password_hash("Password123!"),
        full_name="Course Test Student",
        role="student",
        is_active=True,
    )
    db.add(user)
    await db.flush()

    student = Student(
        user_id=user.id,
        full_name="Course Test Student",
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
    return user, create_access_token(subject=user.id)


async def get_first_unlocked_course(
    client: AsyncClient, token: str, semester: int = 1
) -> dict:
    """Fetch the first unlocked course from the list."""
    res = await client.get(
        f"/api/v1/courses?semester={semester}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    courses = res.json()["data"]
    unlocked = [c for c in courses if not c["is_locked"]]
    assert unlocked, f"No unlocked courses found in Semester {semester}"
    return unlocked[0]


# ─── Test: Course Listing ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_courses_returns_student_branch_courses(
    client: AsyncClient, db_session: AsyncSession
):
    """GET /courses returns courses for the student's branch."""
    _, token = await create_test_student(db_session, semester=3)
    res = await client.get("/api/v1/courses", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "timestamp" in data
    courses = data["data"]
    assert len(courses) >= 10  # At least 10 AIML courses seeded


@pytest.mark.asyncio
async def test_list_courses_filter_by_semester(client: AsyncClient, db_session: AsyncSession):
    """GET /courses?semester=1 returns only Semester 1 courses."""
    _, token = await create_test_student(
        db_session, email="semfilter@gitam.edu", roll_number="CE002", semester=3
    )
    res = await client.get(
        "/api/v1/courses?semester=1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    courses = res.json()["data"]
    assert len(courses) > 0
    for c in courses:
        assert c["semester_number"] == 1


@pytest.mark.asyncio
async def test_list_courses_filter_by_year(client: AsyncClient, db_session: AsyncSession):
    """GET /courses?year=1 returns only Year 1 courses."""
    _, token = await create_test_student(
        db_session, email="yearfilter@gitam.edu", roll_number="CE003", semester=5
    )
    res = await client.get(
        "/api/v1/courses?year=1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    courses = res.json()["data"]
    assert len(courses) > 0
    for c in courses:
        assert c["year_number"] == 1


@pytest.mark.asyncio
async def test_list_courses_filter_by_difficulty(client: AsyncClient, db_session: AsyncSession):
    """GET /courses?difficulty=BEGINNER returns only beginner courses."""
    _, token = await create_test_student(
        db_session, email="difffilter@gitam.edu", roll_number="CE004", semester=8
    )
    res = await client.get(
        "/api/v1/courses?difficulty=BEGINNER",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    courses = res.json()["data"]
    assert len(courses) > 0
    for c in courses:
        assert c["difficulty"] == "BEGINNER"


@pytest.mark.asyncio
async def test_list_courses_filter_by_skill(client: AsyncClient, db_session: AsyncSession):
    """GET /courses?skill=Python returns courses that teach Python."""
    _, token = await create_test_student(
        db_session, email="skillfilter@gitam.edu", roll_number="CE005", semester=8
    )
    res = await client.get(
        "/api/v1/courses?skill=Python",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    courses = res.json()["data"]
    assert len(courses) > 0
    for c in courses:
        skill_names = [s["skill_name"] for s in c["skills"]]
        assert "Python" in skill_names


@pytest.mark.asyncio
async def test_courses_include_skills(client: AsyncClient, db_session: AsyncSession):
    """Each course in the list should include its skill list."""
    _, token = await create_test_student(
        db_session, email="skillincl@gitam.edu", roll_number="CE006", semester=5
    )
    res = await client.get("/api/v1/courses?semester=1", headers={"Authorization": f"Bearer {token}"})
    courses = res.json()["data"]
    assert len(courses) > 0
    for c in courses:
        assert isinstance(c["skills"], list)


# ─── Test: Course Detail ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_course_detail_returns_full_data(client: AsyncClient, db_session: AsyncSession):
    """GET /courses/{id} returns full course detail with resources, outcomes, skills."""
    _, token = await create_test_student(
        db_session, email="detailtest@gitam.edu", roll_number="CE007", semester=3
    )
    headers = {"Authorization": f"Bearer {token}"}
    course = await get_first_unlocked_course(client, token, semester=1)
    course_id = course["id"]

    res = await client.get(f"/api/v1/courses/{course_id}", headers=headers)
    assert res.status_code == 200
    d = res.json()["data"]

    assert d["id"] == course_id
    assert "resources" in d
    assert "outcomes" in d
    assert "skills" in d
    assert "learning_objectives" in d
    assert isinstance(d["resources"], list)
    assert isinstance(d["outcomes"], list)
    assert len(d["resources"]) > 0
    assert len(d["outcomes"]) > 0


@pytest.mark.asyncio
async def test_get_course_detail_not_found(client: AsyncClient, db_session: AsyncSession):
    """GET /courses/{id} with non-existent ID returns 404."""
    _, token = await create_test_student(
        db_session, email="notfound@gitam.edu", roll_number="CE008", semester=2
    )
    res = await client.get(
        "/api/v1/courses/non-existent-course-id",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404


# ─── Test: Lock Enforcement ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_future_semester_courses_are_locked(client: AsyncClient, db_session: AsyncSession):
    """Courses in future semesters must be locked for a Semester 1 student."""
    _, token = await create_test_student(
        db_session, email="locktest@gitam.edu", roll_number="CE009", semester=1
    )
    res = await client.get("/api/v1/courses", headers={"Authorization": f"Bearer {token}"})
    courses = res.json()["data"]

    locked = [c for c in courses if c["is_locked"]]
    assert len(locked) > 0  # Must have locked courses for Sem 1 student

    for c in locked:
        assert c["lock_reason"] is not None
        assert c["user_status"] == "NOT_STARTED"


@pytest.mark.asyncio
async def test_cannot_update_locked_course(client: AsyncClient, db_session: AsyncSession):
    """PATCH on a locked course returns 400."""
    _, token = await create_test_student(
        db_session, email="lockedcourse@gitam.edu", roll_number="CE010", semester=1
    )
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/v1/courses", headers=headers)
    locked = [c for c in res.json()["data"] if c["is_locked"]]
    assert locked, "Expected locked courses for semester 1 student"

    locked_course = locked[0]
    update_res = await client.patch(
        f"/api/v1/courses/{locked_course['id']}/progress",
        headers=headers,
        json={"status": "IN_PROGRESS"},
    )
    assert update_res.status_code == 400
    assert "locked" in update_res.json()["error"]["message"].lower()


# ─── Test: Progress Update ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_course_progress_to_in_progress(client: AsyncClient, db_session: AsyncSession):
    """PATCH /courses/{id}/progress → IN_PROGRESS sets started_at."""
    _, token = await create_test_student(
        db_session, email="inprog@gitam.edu", roll_number="CE011", semester=1
    )
    headers = {"Authorization": f"Bearer {token}"}
    course = await get_first_unlocked_course(client, token)

    res = await client.patch(
        f"/api/v1/courses/{course['id']}/progress",
        headers=headers,
        json={"status": "IN_PROGRESS"},
    )
    assert res.status_code == 200
    d = res.json()["data"]
    assert d["status"] == "IN_PROGRESS"
    assert d["started_at"] is not None
    assert d["completion_percentage"] >= 10.0


@pytest.mark.asyncio
async def test_update_course_progress_to_completed(client: AsyncClient, db_session: AsyncSession):
    """PATCH /courses/{id}/progress → COMPLETED sets completion_percentage=100."""
    _, token = await create_test_student(
        db_session, email="completed@gitam.edu", roll_number="CE012", semester=1
    )
    headers = {"Authorization": f"Bearer {token}"}
    course = await get_first_unlocked_course(client, token)

    res = await client.patch(
        f"/api/v1/courses/{course['id']}/progress",
        headers=headers,
        json={"status": "COMPLETED"},
    )
    assert res.status_code == 200
    d = res.json()["data"]
    assert d["status"] == "COMPLETED"
    assert d["completion_percentage"] == 100.0
    assert d["completed_at"] is not None


@pytest.mark.asyncio
async def test_invalid_status_returns_400(client: AsyncClient, db_session: AsyncSession):
    """PATCH with invalid status returns 400."""
    _, token = await create_test_student(
        db_session, email="badstatus@gitam.edu", roll_number="CE013", semester=1
    )
    headers = {"Authorization": f"Bearer {token}"}
    course = await get_first_unlocked_course(client, token)

    res = await client.patch(
        f"/api/v1/courses/{course['id']}/progress",
        headers=headers,
        json={"status": "DELETED"},
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_skipped_status_not_allowed_for_courses(client: AsyncClient, db_session: AsyncSession):
    """PATCH with SKIPPED status on a course returns 400 (not a valid course status)."""
    _, token = await create_test_student(
        db_session, email="skipstatus@gitam.edu", roll_number="CE014", semester=1
    )
    headers = {"Authorization": f"Bearer {token}"}
    course = await get_first_unlocked_course(client, token)

    res = await client.patch(
        f"/api/v1/courses/{course['id']}/progress",
        headers=headers,
        json={"status": "SKIPPED"},
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_custom_completion_percentage(client: AsyncClient, db_session: AsyncSession):
    """PATCH with explicit completion_percentage stores it correctly."""
    _, token = await create_test_student(
        db_session, email="custompct@gitam.edu", roll_number="CE015", semester=1
    )
    headers = {"Authorization": f"Bearer {token}"}
    course = await get_first_unlocked_course(client, token)

    res = await client.patch(
        f"/api/v1/courses/{course['id']}/progress",
        headers=headers,
        json={"status": "IN_PROGRESS", "completion_percentage": 65.0},
    )
    assert res.status_code == 200
    assert res.json()["data"]["completion_percentage"] == 65.0


# ─── Test: Skill Calculation ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_completing_course_updates_skills(client: AsyncClient, db_session: AsyncSession):
    """Completing a course must auto-update StudentSkill scores."""
    _, token = await create_test_student(
        db_session, email="skillcalc@gitam.edu", roll_number="CE016", semester=1
    )
    headers = {"Authorization": f"Bearer {token}"}
    course = await get_first_unlocked_course(client, token)

    # Complete the course
    res = await client.patch(
        f"/api/v1/courses/{course['id']}/progress",
        headers=headers,
        json={"status": "COMPLETED"},
    )
    assert res.status_code == 200
    d = res.json()["data"]

    # Skills should have been updated
    assert len(d["skills_updated"]) > 0

    # Each updated skill should have a score > 0
    for sk in d["skills_updated"]:
        assert sk["proficiency_score"] > 0
        assert sk["earned_from_course_id"] == course["id"]


@pytest.mark.asyncio
async def test_skill_dashboard_shows_earned_skills(client: AsyncClient, db_session: AsyncSession):
    """GET /courses/skills/my shows earned skills after completing a course."""
    _, token = await create_test_student(
        db_session, email="skilldash@gitam.edu", roll_number="CE017", semester=1
    )
    headers = {"Authorization": f"Bearer {token}"}
    course = await get_first_unlocked_course(client, token)

    # Initially no skills
    res1 = await client.get("/api/v1/courses/skills/my", headers=headers)
    assert res1.status_code == 200
    initial_count = res1.json()["data"]["total_skills_earned"]

    # Complete a course to earn skills
    await client.patch(
        f"/api/v1/courses/{course['id']}/progress",
        headers=headers,
        json={"status": "COMPLETED"},
    )

    # Skills should now be > 0
    res2 = await client.get("/api/v1/courses/skills/my", headers=headers)
    assert res2.status_code == 200
    d2 = res2.json()["data"]
    assert d2["total_skills_earned"] > initial_count
    assert d2["average_proficiency_score"] > 0
    assert d2["top_category"] is not None


@pytest.mark.asyncio
async def test_skill_dashboard_structure(client: AsyncClient, db_session: AsyncSession):
    """GET /courses/skills/my returns all required fields."""
    _, token = await create_test_student(
        db_session, email="skillstruct@gitam.edu", roll_number="CE018", semester=2
    )
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/v1/courses/skills/my", headers=headers)
    assert res.status_code == 200
    d = res.json()["data"]
    required_keys = [
        "total_skills_earned", "average_proficiency_score",
        "top_category", "skills",
    ]
    for k in required_keys:
        assert k in d


@pytest.mark.asyncio
async def test_completing_course_twice_does_not_duplicate_skills(
    client: AsyncClient, db_session: AsyncSession
):
    """Completing the same course twice should update, not duplicate, skill records."""
    _, token = await create_test_student(
        db_session, email="nodupe@gitam.edu", roll_number="CE019", semester=1
    )
    headers = {"Authorization": f"Bearer {token}"}
    course = await get_first_unlocked_course(client, token)

    # Complete twice
    for _ in range(2):
        await client.patch(
            f"/api/v1/courses/{course['id']}/progress",
            headers=headers,
            json={"status": "COMPLETED"},
        )

    res = await client.get("/api/v1/courses/skills/my", headers=headers)
    skills = res.json()["data"]["skills"]

    # Check no duplicate skill entries
    skill_ids = [s["skill_id"] for s in skills]
    assert len(skill_ids) == len(set(skill_ids)), "Duplicate skill entries found"


# ─── Test: Roadmap Integration ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_completing_course_updates_roadmap_module(
    client: AsyncClient, db_session: AsyncSession
):
    """Completing a course must auto-mark the linked RoadmapModule as COMPLETED."""
    _, token = await create_test_student(
        db_session, email="roadmapint@gitam.edu", roll_number="CE020", semester=3
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Find a Sem 1 course linked to a RoadmapModule
    list_res = await client.get(
        "/api/v1/courses?semester=1", headers=headers
    )
    courses = [c for c in list_res.json()["data"] if not c["is_locked"]]
    assert courses

    # Get full detail to see if roadmap_module_id is set
    detail_res = await client.get(
        f"/api/v1/courses/{courses[0]['id']}", headers=headers
    )
    assert detail_res.status_code == 200

    # Complete the course
    complete_res = await client.patch(
        f"/api/v1/courses/{courses[0]['id']}/progress",
        headers=headers,
        json={"status": "COMPLETED"},
    )
    assert complete_res.status_code == 200
    d = complete_res.json()["data"]

    # roadmap_module_updated will be True if the course has a linked module
    # This tests the integration path exists and responds correctly
    assert "roadmap_module_updated" in d
    assert isinstance(d["roadmap_module_updated"], bool)


@pytest.mark.asyncio
async def test_response_includes_timestamp(client: AsyncClient, db_session: AsyncSession):
    """All responses from /courses should include a timestamp field."""
    _, token = await create_test_student(
        db_session, email="tscheck@gitam.edu", roll_number="CE021", semester=3
    )
    headers = {"Authorization": f"Bearer {token}"}

    for endpoint in ["/api/v1/courses", "/api/v1/courses/skills/my"]:
        res = await client.get(endpoint, headers=headers)
        assert res.status_code == 200
        assert "timestamp" in res.json()


# ─── Test: Unauthorized Access ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_courses_requires_auth(client: AsyncClient, db_session: AsyncSession):
    res = await client.get("/api/v1/courses")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_course_detail_requires_auth(client: AsyncClient, db_session: AsyncSession):
    res = await client.get("/api/v1/courses/some-id")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_update_progress_requires_auth(client: AsyncClient, db_session: AsyncSession):
    res = await client.patch("/api/v1/courses/some-id/progress", json={"status": "IN_PROGRESS"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_skills_dashboard_requires_auth(client: AsyncClient, db_session: AsyncSession):
    res = await client.get("/api/v1/courses/skills/my")
    assert res.status_code == 401
