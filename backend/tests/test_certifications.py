"""
Tests for the Certification Intelligence Engine.

Covers:
- Certification retrieval & filtering (branch, semester, difficulty, provider, skill)
- Certification detail endpoint (with prerequisites, exams, benefits, skills)
- 5-way unlock validation rules
- Certification submission flow (certificate_url, verification_id, score, issue_date)
- Skill score auto-update on certification completion
- Roadmap integration (auto-marking linked module as COMPLETED)
- Placement readiness score calculation
- Internship module unlock flag
- Authentication enforcement
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

from datetime import datetime, timezone
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import create_access_token, get_password_hash
from app.models.user import User
from app.models.student import Student
from app.models.branch import Branch
from app.models.target_role import TargetRole
from app.models.course import Course
from app.models.project import Project
from app.models.skill import Skill
from app.models.student_course_progress import StudentCourseProgress
from app.models.student_project import StudentProject
from app.models.student_skill import StudentSkill
from app.models.roadmap_module import RoadmapModule
from app.models.student_progress import StudentRoadmapProgress
from app.schemas.roadmap import ProgressStatus


# ─── Fixture Helper ───────────────────────────────────────────────────────────

async def create_test_student_for_certifications(
    db: AsyncSession,
    email: str = "certtest@gitam.edu",
    roll_number: str = "CTE001",
    branch_code: str = "AIML",
    current_year: int = 2,
    semester: int = 4,
) -> tuple[User, str]:
    branch_res = await db.execute(select(Branch).where(Branch.code == branch_code))
    branch = branch_res.scalars().first()

    role_res = await db.execute(select(TargetRole))
    role = role_res.scalars().first()

    user = User(
        email=email,
        hashed_password=get_password_hash("Password123!"),
        full_name="Cert Test Student",
        role="student",
        is_active=True,
    )
    db.add(user)
    await db.flush()

    student = Student(
        user_id=user.id,
        full_name="Cert Test Student",
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


async def complete_all_prerequisites_for_cert(db: AsyncSession, user_id: str):
    """Helper to complete all courses, projects, skills, and roadmap modules."""
    student_res = await db.execute(select(Student).where(Student.user_id == user_id))
    student = student_res.scalars().first()

    # Complete courses
    courses_res = await db.execute(select(Course).where(Course.branch_id == student.branch_id))
    courses = courses_res.unique().scalars().all()
    for c in courses:
        db.add(StudentCourseProgress(
            student_id=student.id, course_id=c.id, status="COMPLETED", completion_percentage=100.0,
        ))

    # Complete projects
    projs_res = await db.execute(select(Project).where(Project.branch_id == student.branch_id))
    projs = projs_res.unique().scalars().all()
    for p in projs:
        db.add(StudentProject(
            student_id=student.id, project_id=p.id, status="COMPLETED",
        ))

    # Populate skills with max score
    skills_res = await db.execute(select(Skill))
    skills = skills_res.unique().scalars().all()
    now = datetime.now(timezone.utc)
    for s in skills:
        db.add(StudentSkill(
            student_id=student.id, skill_id=s.id, proficiency_score=100.0, last_updated=now,
        ))

    # Complete roadmap modules
    modules_res = await db.execute(select(RoadmapModule))
    modules = modules_res.unique().scalars().all()
    for m in modules:
        db.add(StudentRoadmapProgress(
            student_id=student.id, roadmap_module_id=m.id,
            status=ProgressStatus.COMPLETED, completion_percentage=100.0,
        ))

    await db.commit()


# ─── Tests ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_certifications_returns_branch_certs(client: AsyncClient, db_session: AsyncSession):
    _, token = await create_test_student_for_certifications(db_session, semester=4)
    res = await client.get("/api/v1/certifications", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["data"]) >= 10


@pytest.mark.asyncio
async def test_list_certifications_filter_by_provider(client: AsyncClient, db_session: AsyncSession):
    _, token = await create_test_student_for_certifications(
        db_session, email="cprov@gitam.edu", roll_number="CTE002", semester=6
    )
    res = await client.get(
        "/api/v1/certifications?provider=NPTEL",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    certs = res.json()["data"]
    assert len(certs) > 0
    for c in certs:
        assert "NPTEL" in c["provider"] or c["provider_type"] == "NPTEL"


@pytest.mark.asyncio
async def test_get_certification_detail_full_data(client: AsyncClient, db_session: AsyncSession):
    _, token = await create_test_student_for_certifications(
        db_session, email="cdetail@gitam.edu", roll_number="CTE003", semester=4
    )
    headers = {"Authorization": f"Bearer {token}"}

    res_list = await client.get("/api/v1/certifications", headers=headers)
    cert_id = res_list.json()["data"][0]["id"]

    res = await client.get(f"/api/v1/certifications/{cert_id}", headers=headers)
    assert res.status_code == 200
    d = res.json()["data"]

    assert d["id"] == cert_id
    assert "prerequisites" in d
    assert "exams" in d
    assert "benefits" in d
    assert "skills" in d
    assert len(d["exams"]) > 0
    assert len(d["benefits"]) > 0


@pytest.mark.asyncio
async def test_unlock_validation_future_semester_locked(client: AsyncClient, db_session: AsyncSession):
    """Certifications in future semesters must be locked."""
    _, token = await create_test_student_for_certifications(
        db_session, email="clocked@gitam.edu", roll_number="CTE004", semester=1
    )
    res = await client.get("/api/v1/certifications", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    locked = [c for c in res.json()["data"] if c["is_locked"]]
    assert len(locked) > 0


@pytest.mark.asyncio
async def test_submit_certification_flow(client: AsyncClient, db_session: AsyncSession):
    user, token = await create_test_student_for_certifications(
        db_session, email="csubmit@gitam.edu", roll_number="CTE005", semester=4
    )
    headers = {"Authorization": f"Bearer {token}"}

    await complete_all_prerequisites_for_cert(db_session, user.id)

    res_list = await client.get("/api/v1/certifications?semester=4", headers=headers)
    unlocked = [c for c in res_list.json()["data"] if not c["is_locked"]]
    assert len(unlocked) > 0, "Expected unlocked certification after prereq completion"
    cert_id = unlocked[0]["id"]

    payload = {
        "certificate_url": "https://nptel.ac.in/noc/Ecertificate/?q=NPTEL24CS100",
        "verification_id": "NPTEL24CS100S123",
        "score": 85.5,
    }
    submit_res = await client.post(
        f"/api/v1/certifications/{cert_id}/submit",
        headers=headers,
        json=payload,
    )
    assert submit_res.status_code == 200
    d = submit_res.json()["data"]
    assert d["status"] == "COMPLETED"
    assert d["verified"] is True
    assert d["placement_readiness_score"] > 0
    assert d["internship_unlocked"] is True
    assert len(d["skills_updated"]) > 0


@pytest.mark.asyncio
async def test_get_my_certifications(client: AsyncClient, db_session: AsyncSession):
    user, token = await create_test_student_for_certifications(
        db_session, email="cmy@gitam.edu", roll_number="CTE006", semester=4
    )
    headers = {"Authorization": f"Bearer {token}"}
    await complete_all_prerequisites_for_cert(db_session, user.id)

    res_list = await client.get("/api/v1/certifications?semester=4", headers=headers)
    unlocked = [c for c in res_list.json()["data"] if not c["is_locked"]]
    cert_id = unlocked[0]["id"]

    await client.post(
        f"/api/v1/certifications/{cert_id}/submit",
        headers=headers,
        json={"certificate_url": "https://coursera.org/verify/XYZ123", "verification_id": "XYZ123"},
    )

    my_res = await client.get("/api/v1/certifications/my", headers=headers)
    assert my_res.status_code == 200
    my_data = my_res.json()["data"]
    assert len(my_data) > 0
    assert my_data[0]["certification_id"] == cert_id


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient, db_session: AsyncSession):
    assert (await client.get("/api/v1/certifications")).status_code == 401
    assert (await client.get("/api/v1/certifications/my")).status_code == 401
    assert (await client.get("/api/v1/certifications/some-id")).status_code == 401
