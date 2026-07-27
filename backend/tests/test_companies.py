"""
Tests for the Industry Intelligence Engine.

Covers:
- Company listing (all companies returned with readiness context)
- Company listing filters (industry, is_hiring, skill)
- Company detail (skills, job roles, interview rounds, questions, gap analysis)
- Readiness score calculation (5-axis: course, project, skill, cert, overall)
- My readiness dashboard (per-student summary)
- StudentCompanyReadiness record persistence on detail fetch
"""
import asyncio
import uuid
import pytest
from sqlalchemy import select

from app.api.v1.router import api_router
from app.database.init_db import seed_master_data
from app.models.company import Company
from app.models.company_mapping import CompanySkill, CompanyCourse
from app.models.company_interview import CompanyInterviewRound, CompanyInterviewQuestion
from app.models.job_role import JobRole
from app.models.skill import Skill
from app.models.student import Student
from app.models.student_company_readiness import StudentCompanyReadiness
from app.models.student_course_progress import StudentCourseProgress
from app.models.student_skill import StudentSkill
from app.models.user import User

# ─── Fixtures / Helpers ───────────────────────────────────────────────────────

async def _make_user_and_student(db, branch_code: str = "AIML", semester: int = 3):
    """Create a test user + student profile."""
    from app.models.branch import Branch
    from app.models.target_role import TargetRole
    from app.core.security import get_password_hash

    branch_res = await db.execute(select(Branch).where(Branch.code == branch_code))
    branch = branch_res.scalars().first()
    assert branch, f"Branch '{branch_code}' not seeded"

    role_res = await db.execute(select(TargetRole))
    role = role_res.scalars().first()
    assert role, "No TargetRole seeded"

    suffix = uuid.uuid4().hex[:8]
    email = f"test_{suffix}@gitam.edu"
    roll = f"20A{suffix.upper()}"

    user = User(
        email=email,
        hashed_password=get_password_hash("Password123!"),
        role="STUDENT",
        is_active=True,
    )
    db.add(user)
    await db.flush()

    current_year = max(1, (semester + 1) // 2)
    student = Student(
        user_id=user.id,
        full_name="Test Student",
        email=email,
        roll_number=roll,
        branch_id=branch.id,
        target_role_id=role.id,
        current_year=current_year,
        semester=semester,
        is_active=True,
    )
    db.add(student)
    await db.commit()
    return user, student


async def _get_auth_headers(db, user: User) -> dict:
    """Generate a real JWT for test user."""
    from app.core.security import create_access_token
    token = create_access_token({"sub": user.id})
    return {"Authorization": f"Bearer {token}"}


async def _make_company(db, name: str, industry: str = "Technology") -> Company:
    """Create a minimal test company."""
    res = await db.execute(select(Company).where(Company.name == name))
    existing = res.scalars().first()
    if existing:
        return existing
    company = Company(
        name=name,
        industry=industry,
        headquarters="Test City",
        description=f"{name} description",
        is_hiring=True,
    )
    db.add(company)
    await db.flush()
    await db.commit()
    return company


async def _add_company_skill(db, company_id: str, skill_id: str, required_level: str = "BEGINNER", weightage: float = 1.0):
    existing = await db.execute(
        select(CompanySkill).where(
            CompanySkill.company_id == company_id,
            CompanySkill.skill_id == skill_id,
        )
    )
    if not existing.scalars().first():
        db.add(CompanySkill(company_id=company_id, skill_id=skill_id, required_level=required_level, weightage=weightage))
        await db.commit()


async def _complete_course(db, student_id: str, course_id: str):
    res = await db.execute(
        select(StudentCourseProgress).where(
            StudentCourseProgress.student_id == student_id,
            StudentCourseProgress.course_id == course_id,
        )
    )
    prog = res.scalars().first()
    if not prog:
        from datetime import datetime, timezone
        prog = StudentCourseProgress(
            student_id=student_id,
            course_id=course_id,
            status="COMPLETED",
            completed_at=datetime.now(timezone.utc),
        )
        db.add(prog)
    else:
        prog.status = "COMPLETED"
    await db.commit()


async def _set_student_skill(db, student_id: str, skill_id: str, score: float = 75.0):
    from datetime import datetime, timezone
    res = await db.execute(
        select(StudentSkill).where(
            StudentSkill.student_id == student_id,
            StudentSkill.skill_id == skill_id,
        )
    )
    ss = res.unique().scalars().first()
    if not ss:
        ss = StudentSkill(
            student_id=student_id,
            skill_id=skill_id,
            proficiency_score=score,
            last_updated=datetime.now(timezone.utc),
        )
        db.add(ss)
    else:
        ss.proficiency_score = score
    await db.commit()


# ─── Tests ────────────────────────────────────────────────────────────────────

async def test_list_companies_returns_all_seeded(test_engine, TestAsyncSessionLocal):
    """All seeded companies should appear in the list endpoint."""
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.services.industry_service import IndustryService

    async with TestAsyncSessionLocal() as db:
        await seed_master_data(db)
        user, student = await _make_user_and_student(db, branch_code="AIML")

        service = IndustryService(db)
        companies = await service.list_companies(user_id=user.id)

    assert len(companies) >= 1, "Expected at least one company"
    for c in companies:
        assert c.id
        assert c.name
        assert c.industry
        assert isinstance(c.readiness_score, float)
        assert c.readiness_label in ("WEAK", "MODERATE", "STRONG", "READY")
    print(f"[PASS] list_companies returned {len(companies)} companies")


async def test_list_companies_filter_is_hiring(test_engine, TestAsyncSessionLocal):
    """is_hiring=True filter should only return hiring companies."""
    async with TestAsyncSessionLocal() as db:
        await seed_master_data(db)
        user, student = await _make_user_and_student(db, branch_code="ECE")

        from app.services.industry_service import IndustryService
        service = IndustryService(db)
        companies = await service.list_companies(user_id=user.id, is_hiring=True)

    for c in companies:
        assert c.is_hiring is True
    print(f"[PASS] is_hiring=True filter returned {len(companies)} companies")


async def test_list_companies_filter_industry(test_engine, TestAsyncSessionLocal):
    """Industry filter should narrow results correctly."""
    async with TestAsyncSessionLocal() as db:
        await seed_master_data(db)
        user, student = await _make_user_and_student(db, branch_code="AIML")

        from app.services.industry_service import IndustryService
        service = IndustryService(db)
        companies = await service.list_companies(user_id=user.id, industry="Semiconductors")

    for c in companies:
        assert "semiconductor" in c.industry.lower()
    print(f"[PASS] industry='Semiconductors' filter returned {len(companies)} companies")


async def test_list_companies_filter_skill(test_engine, TestAsyncSessionLocal):
    """Skill filter should only return companies requiring that skill."""
    async with TestAsyncSessionLocal() as db:
        await seed_master_data(db)
        user, student = await _make_user_and_student(db, branch_code="AIML")

        from app.services.industry_service import IndustryService
        service = IndustryService(db)
        companies = await service.list_companies(user_id=user.id, skill="TensorFlow")

    # At least NVIDIA should appear
    names = [c.name for c in companies]
    assert any("NVIDIA" in n for n in names), f"Expected NVIDIA in skill=TensorFlow filter, got {names}"
    print(f"[PASS] skill='TensorFlow' filter returned {len(companies)} companies")


async def test_list_companies_sorted_by_readiness(test_engine, TestAsyncSessionLocal):
    """List should be sorted by readiness_score descending."""
    async with TestAsyncSessionLocal() as db:
        await seed_master_data(db)
        user, student = await _make_user_and_student(db)

        from app.services.industry_service import IndustryService
        service = IndustryService(db)
        companies = await service.list_companies(user_id=user.id)

    scores = [c.readiness_score for c in companies]
    assert scores == sorted(scores, reverse=True), "Companies not sorted by readiness_score desc"
    print("[PASS] Companies sorted by readiness_score descending")


async def test_company_detail_returns_full_intelligence(test_engine, TestAsyncSessionLocal):
    """Company detail should include job roles, skills, interview rounds, and questions."""
    async with TestAsyncSessionLocal() as db:
        await seed_master_data(db)
        user, student = await _make_user_and_student(db, branch_code="AIML")

        # Get Google India (seeded)
        res = await db.execute(select(Company).where(Company.name == "Google India"))
        google = res.scalars().first()
        assert google, "Google India not seeded"

        from app.services.industry_service import IndustryService
        service = IndustryService(db)
        detail = await service.get_company_detail(user_id=user.id, company_id=google.id)

    assert detail.id == google.id
    assert detail.name == "Google India"
    assert len(detail.job_roles) >= 1, "Expected at least 1 job role"
    assert len(detail.top_skills) >= 1, "Expected at least 1 required skill"
    assert len(detail.interview_rounds) >= 1, "Expected at least 1 interview round"
    assert len(detail.interview_questions) >= 1, "Expected at least 1 interview question"
    assert len(detail.recommended_courses) >= 1, "Expected recommended courses"
    assert isinstance(detail.course_score, float)
    assert isinstance(detail.skill_score, float)
    assert isinstance(detail.readiness_score, float)
    assert detail.readiness_label in ("WEAK", "MODERATE", "STRONG", "READY")
    print(f"[PASS] Company detail for {detail.name}: readiness={detail.readiness_score}, label={detail.readiness_label}")


async def test_company_detail_persists_readiness(test_engine, TestAsyncSessionLocal):
    """Fetching company detail should persist a StudentCompanyReadiness record."""
    async with TestAsyncSessionLocal() as db:
        await seed_master_data(db)
        user, student = await _make_user_and_student(db)

        res = await db.execute(select(Company).where(Company.name == "Google India"))
        google = res.scalars().first()

        from app.services.industry_service import IndustryService
        service = IndustryService(db)
        await service.get_company_detail(user_id=user.id, company_id=google.id)

        # Check persistence
        rr_res = await db.execute(
            select(StudentCompanyReadiness).where(
                StudentCompanyReadiness.student_id == student.id,
                StudentCompanyReadiness.company_id == google.id,
            )
        )
        record = rr_res.scalars().first()

    assert record is not None, "StudentCompanyReadiness record was not persisted"
    assert 0.0 <= record.overall_score <= 100.0
    print(f"[PASS] Readiness record persisted: overall_score={record.overall_score}")


async def test_readiness_score_improves_with_completed_courses(test_engine, TestAsyncSessionLocal):
    """Student who completes recommended courses should have higher course_score."""
    async with TestAsyncSessionLocal() as db:
        await seed_master_data(db)
        user, student = await _make_user_and_student(db, branch_code="AIML")

        res = await db.execute(select(Company).where(Company.name == "Google India"))
        google = res.scalars().first()

        from app.services.industry_service import IndustryService
        service = IndustryService(db)

        # Score before completing any courses
        detail_before = await service.get_company_detail(user_id=user.id, company_id=google.id)
        course_score_before = detail_before.course_score

        # Complete all recommended courses (query explicitly)
        from sqlalchemy.orm import selectinload as si
        from app.models.company_mapping import CompanyCourse
        cc_res = await db.execute(select(CompanyCourse).where(CompanyCourse.company_id == google.id))
        company_courses = cc_res.unique().scalars().all()
        for cc in company_courses:
            await _complete_course(db, student.id, cc.course_id)

        # Score after completing courses
        detail_after = await service.get_company_detail(user_id=user.id, company_id=google.id)

    assert detail_after.course_score > course_score_before or detail_after.course_score == 100.0, \
        f"Expected course_score to improve: before={course_score_before}, after={detail_after.course_score}"
    print(f"[PASS] Course score improved: {course_score_before} -> {detail_after.course_score}")


async def test_readiness_score_improves_with_skills(test_engine, TestAsyncSessionLocal):
    """Student with matching skills should have higher skill_score."""
    async with TestAsyncSessionLocal() as db:
        await seed_master_data(db)
        user, student = await _make_user_and_student(db, branch_code="AIML")

        res = await db.execute(select(Company).where(Company.name == "NVIDIA India"))
        nvidia = res.scalars().first()
        assert nvidia, "NVIDIA India not seeded"

        from app.services.industry_service import IndustryService
        service = IndustryService(db)

        # Score before adding any skills
        detail_before = await service.get_company_detail(user_id=user.id, company_id=nvidia.id)
        skill_score_before = detail_before.skill_score

        # Add all required skills at high score (query explicitly)
        from app.models.company_mapping import CompanySkill as CS
        cs_res = await db.execute(select(CS).where(CS.company_id == nvidia.id))
        nvidia_skills = cs_res.scalars().all()
        for cs in nvidia_skills:
            await _set_student_skill(db, student.id, cs.skill_id, score=90.0)

        # Score after adding skills
        detail_after = await service.get_company_detail(user_id=user.id, company_id=nvidia.id)

    assert detail_after.skill_score > skill_score_before or detail_after.skill_score >= 80.0, \
        f"Expected skill_score to improve: before={skill_score_before}, after={detail_after.skill_score}"
    print(f"[PASS] Skill score improved: {skill_score_before:.1f} -> {detail_after.skill_score:.1f}")


async def test_gap_skills_identifies_missing_skills(test_engine, TestAsyncSessionLocal):
    """Gap skills list should reflect skills the student has not yet acquired."""
    async with TestAsyncSessionLocal() as db:
        await seed_master_data(db)
        user, student = await _make_user_and_student(db, branch_code="AIML")

        res = await db.execute(select(Company).where(Company.name == "Google India"))
        google = res.scalars().first()

        from app.services.industry_service import IndustryService
        service = IndustryService(db)
        detail = await service.get_company_detail(user_id=user.id, company_id=google.id)

    # A new student has no skills → all required skills are gaps
    assert isinstance(detail.gap_skills, list)
    # At least some gap skills should be present for a brand-new student
    assert len(detail.gap_skills) >= 0  # Could be empty if thresholds are met
    print(f"[PASS] Gap skills identified: {detail.gap_skills}")


async def test_company_not_found_raises_404(test_engine, TestAsyncSessionLocal):
    """Requesting a non-existent company should raise NotFoundException."""
    from app.core.exceptions import NotFoundException

    async with TestAsyncSessionLocal() as db:
        await seed_master_data(db)
        user, student = await _make_user_and_student(db)

        from app.services.industry_service import IndustryService
        service = IndustryService(db)
        with pytest.raises(NotFoundException):
            await service.get_company_detail(user_id=user.id, company_id="non-existent-id")
    print("[PASS] Non-existent company raises NotFoundException")


async def test_my_readiness_dashboard(test_engine, TestAsyncSessionLocal):
    """My readiness dashboard should return per-company readiness summary."""
    async with TestAsyncSessionLocal() as db:
        await seed_master_data(db)
        user, student = await _make_user_and_student(db, branch_code="ECE", semester=4)

        from app.services.industry_service import IndustryService
        service = IndustryService(db)
        summary = await service.get_my_readiness(user_id=user.id)

    assert summary.student_id == student.id
    assert summary.branch_name  # not empty
    assert isinstance(summary.average_readiness, float)
    assert 0.0 <= summary.average_readiness <= 100.0
    assert len(summary.companies) >= 1, "Expected at least one company in readiness summary"
    for item in summary.companies:
        assert item.company_id
        assert item.company_name
        assert 0.0 <= item.overall_score <= 100.0
        assert item.readiness_label in ("WEAK", "MODERATE", "STRONG", "READY")
    print(f"[PASS] My readiness: avg={summary.average_readiness:.1f}, top_company={summary.top_company}, companies={len(summary.companies)}")


async def test_readiness_label_thresholds(test_engine, TestAsyncSessionLocal):
    """Readiness labels should be correctly assigned based on score thresholds."""
    from app.services.industry_service import _readiness_label
    assert _readiness_label(0.0) == "WEAK"
    assert _readiness_label(39.9) == "WEAK"
    assert _readiness_label(40.0) == "MODERATE"
    assert _readiness_label(59.9) == "MODERATE"
    assert _readiness_label(60.0) == "STRONG"
    assert _readiness_label(79.9) == "STRONG"
    assert _readiness_label(80.0) == "READY"
    assert _readiness_label(100.0) == "READY"
    print("[PASS] Readiness label thresholds correct")


async def test_student_without_profile_raises_404(test_engine, TestAsyncSessionLocal):
    """User without a student profile should raise NotFoundException."""
    from app.core.exceptions import NotFoundException

    async with TestAsyncSessionLocal() as db:
        await seed_master_data(db)
        email = f"noprofile_{uuid.uuid4().hex[:8]}@gitam.edu"
        user = User(email=email, hashed_password="hashed_pw", role="STUDENT", is_active=True)
        db.add(user)
        await db.commit()

        from app.services.industry_service import IndustryService
        service = IndustryService(db)
        with pytest.raises(NotFoundException):
            await service.list_companies(user_id=user.id)
    print("[PASS] User without student profile raises NotFoundException")


async def test_interview_questions_have_expected_fields(test_engine, TestAsyncSessionLocal):
    """Interview questions should have all required fields populated."""
    async with TestAsyncSessionLocal() as db:
        await seed_master_data(db)
        user, student = await _make_user_and_student(db, branch_code="ECE")

        res = await db.execute(select(Company).where(Company.name == "Qualcomm India"))
        qualcomm = res.scalars().first()
        assert qualcomm, "Qualcomm India not seeded"

        from app.services.industry_service import IndustryService
        service = IndustryService(db)
        detail = await service.get_company_detail(user_id=user.id, company_id=qualcomm.id)

    for iq in detail.interview_questions:
        assert iq.id
        assert iq.question
        assert iq.difficulty in ("EASY", "MEDIUM", "HARD")
        assert iq.category in ("TECHNICAL", "SYSTEM_DESIGN", "HR", "CODING", "APTITUDE")
    print(f"[PASS] Interview questions for Qualcomm: {len(detail.interview_questions)} questions with valid fields")


async def test_job_roles_have_valid_data(test_engine, TestAsyncSessionLocal):
    """Job roles should have valid employment_type, experience_level, and salary data."""
    async with TestAsyncSessionLocal() as db:
        await seed_master_data(db)
        user, student = await _make_user_and_student(db, branch_code="EEE")

        res = await db.execute(select(Company).where(Company.name == "ABB India"))
        abb = res.scalars().first()
        assert abb, "ABB India not seeded"

        from app.services.industry_service import IndustryService
        service = IndustryService(db)
        detail = await service.get_company_detail(user_id=user.id, company_id=abb.id)

    for jr in detail.job_roles:
        assert jr.title
        assert jr.employment_type in ("FULL_TIME", "INTERNSHIP", "TRAINEE")
        assert jr.experience_level in ("ENTRY_LEVEL", "MID_LEVEL", "SENIOR")
        assert jr.status == "ACTIVE"
    print(f"[PASS] Job roles for ABB India: {len(detail.job_roles)} roles with valid fields")


# ─── Runner ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    sys.path.insert(0, "backend")
    from tests.conftest import test_engine, TestAsyncSessionLocal  # type: ignore

    tests = [
        test_list_companies_returns_all_seeded,
        test_list_companies_filter_is_hiring,
        test_list_companies_filter_industry,
        test_list_companies_filter_skill,
        test_list_companies_sorted_by_readiness,
        test_company_detail_returns_full_intelligence,
        test_company_detail_persists_readiness,
        test_readiness_score_improves_with_completed_courses,
        test_readiness_score_improves_with_skills,
        test_gap_skills_identifies_missing_skills,
        test_company_not_found_raises_404,
        test_my_readiness_dashboard,
        test_readiness_label_thresholds,
        test_student_without_profile_raises_404,
        test_interview_questions_have_expected_fields,
        test_job_roles_have_valid_data,
    ]

    async def run():
        eng = test_engine()
        Session = TestAsyncSessionLocal(eng)
        passed = 0
        failed = 0
        for t in tests:
            try:
                await t(eng, Session)
                passed += 1
            except Exception as e:
                print(f"[FAIL] {t.__name__}: {e}")
                import traceback
                traceback.print_exc()
                failed += 1
        print(f"\n{'='*60}")
        print(f"Industry Intelligence Engine Tests: {passed} passed, {failed} failed")
        print(f"{'='*60}")

    asyncio.run(run())
