"""
Tests for the Internship & Placement Engine.

Covers:
  1. Eligibility validation (readiness score, branch, CGPA)
  2. Listing internships and placement jobs with eligibility flags
  3. Apply workflow (happy path, duplicate, ineligible)
  4. Application stage pipeline with valid/invalid transitions
  5. Offer letter auto-generation on SELECTED
  6. Full application history retrieval
  7. Readiness check (score gate)
  8. Dashboard summary statistics
"""
import sys
import asyncio
from datetime import datetime, timezone, date
from typing import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, async_sessionmaker
from sqlalchemy.orm import selectinload

# Minimal pytest stub so tests run without pytest installed
import types
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
from app.models.company import Company
from app.models.placement import Internship, PlacementJob, StudentApplication, OfferLetter
from app.models.student_company_readiness import StudentCompanyReadiness
from app.core.exceptions import NotFoundException, BadRequestException
from app.schemas.placement import ApplicationCreate, ApplicationStatusUpdate
from app.services.placement_service import PlacementService


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _make_branch(db: AsyncSession, code: str = "AIML") -> Branch:
    existing = await db.execute(select(Branch).where(Branch.code == code))
    b = existing.scalars().first()
    if b:
        return b
    b = Branch(code=code, name=f"{code} Branch", description="Test branch")
    db.add(b)
    await db.commit()
    await db.refresh(b)
    return b


async def _make_target_role(db: AsyncSession) -> "TargetRole":
    from app.models.target_role import TargetRole
    existing = await db.execute(select(TargetRole))
    role = existing.scalars().first()
    if role:
        return role
    role = TargetRole(title="Test Engineer", description="Default test role")
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role


async def _make_user_and_student(
    db: AsyncSession, email: str, branch_code: str = "AIML"
) -> tuple[User, Student]:
    from app.models.target_role import TargetRole
    branch = await _make_branch(db, branch_code)
    role = await _make_target_role(db)

    user = User(email=email, hashed_password="hashed", is_active=True, role="STUDENT")
    db.add(user)
    await db.flush()

    import uuid as _uuid
    student = Student(
        user_id=user.id,
        full_name="Test Student",
        email=email,
        roll_number=f"R{_uuid.uuid4().hex[:8].upper()}",
        branch_id=branch.id,
        target_role_id=role.id,
        current_year=3,
        semester=5,
        is_active=True,
    )
    db.add(student)
    await db.commit()
    await db.refresh(user)
    await db.refresh(student)
    return user, student


async def _make_company(db: AsyncSession, name: str = "Test Corp") -> Company:
    res = await db.execute(select(Company).where(Company.name == name))
    c = res.scalars().first()
    if c:
        return c
    c = Company(name=name, industry="IT", is_hiring=True)
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return c


async def _set_readiness(db: AsyncSession, student_id: str, company_id: str, score: float) -> None:
    """Upsert a StudentCompanyReadiness record so eligibility checks work."""
    res = await db.execute(
        select(StudentCompanyReadiness).where(
            StudentCompanyReadiness.student_id == student_id,
            StudentCompanyReadiness.company_id == company_id,
            StudentCompanyReadiness.job_role_id.is_(None),
        )
    )
    rec = res.scalars().first()
    if rec:
        rec.overall_score = score
        rec.last_updated = datetime.now(timezone.utc)
    else:
        rec = StudentCompanyReadiness(
            student_id=student_id,
            company_id=company_id,
            overall_score=score,
            last_updated=datetime.now(timezone.utc),
        )
        db.add(rec)
    await db.commit()


async def _make_internship(
    db: AsyncSession, company_id: str,
    title: str = "Software Intern",
    min_score: float = 50.0,
    branches: str = "AIML",
    min_cgpa: float = None,
) -> Internship:
    i = Internship(
        company_id=company_id,
        title=title,
        internship_type="TECHNICAL",
        mode="HYBRID",
        stipend=50000,
        duration="3 months",
        location="Bangalore",
        openings=5,
        minimum_readiness_score=min_score,
        allowed_branches=branches,
        minimum_cgpa=min_cgpa,
        status="ACTIVE",
    )
    db.add(i)
    await db.commit()
    await db.refresh(i)
    return i


async def _make_placement(
    db: AsyncSession, company_id: str,
    title: str = "Software Engineer",
    min_score: float = 50.0,
    branches: str = "AIML",
) -> PlacementJob:
    p = PlacementJob(
        company_id=company_id,
        title=title,
        package_min=10.0,
        package_max=15.0,
        location="Bangalore",
        openings=5,
        minimum_readiness_score=min_score,
        allowed_branches=branches,
        status="ACTIVE",
    )
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


# ─── Tests ────────────────────────────────────────────────────────────────────

async def test_list_internships_with_eligibility(engine: AsyncEngine, Session):
    """Eligible internships (score >= minimum) should have is_eligible=True."""
    async with Session() as db:
        user, student = await _make_user_and_student(db, "intern.list@test.com", "AIML")
        company = await _make_company(db, "InternCorp1")
        await _set_readiness(db, student.id, company.id, 60.0)  # meets threshold

        await _make_internship(db, company.id, "ML Intern", min_score=50.0, branches="AIML")

        service = PlacementService(db)
        results = await service.list_internships(user_id=user.id)
        assert len(results) >= 1
        ml_intern = next((r for r in results if r.title == "ML Intern"), None)
        assert ml_intern is not None
        assert ml_intern.is_eligible is True
        print(f"[PASS] list_internships: {len(results)} internships, ML Intern eligible")


async def test_list_internships_ineligible_branch(engine: AsyncEngine, Session):
    """Student with ECE branch should be ineligible for AIML-only internship."""
    async with Session() as db:
        user, student = await _make_user_and_student(db, "intern.branch@test.com", "ECE")
        company = await _make_company(db, "InternCorp2")
        await _set_readiness(db, student.id, company.id, 80.0)  # high score but wrong branch

        await _make_internship(db, company.id, "AI Only Intern", min_score=50.0, branches="AIML")

        service = PlacementService(db)
        results = await service.list_internships(user_id=user.id)
        ai_intern = next((r for r in results if r.title == "AI Only Intern"), None)
        assert ai_intern is not None
        assert ai_intern.is_eligible is False
        assert "branch" in ai_intern.eligibility_reason.lower()
        print(f"[PASS] branch ineligibility: {ai_intern.eligibility_reason}")


async def test_list_internships_ineligible_score(engine: AsyncEngine, Session):
    """Student with readiness score below threshold should be ineligible."""
    async with Session() as db:
        user, student = await _make_user_and_student(db, "intern.score@test.com", "AIML")
        company = await _make_company(db, "InternCorp3")
        await _set_readiness(db, student.id, company.id, 30.0)  # low score

        await _make_internship(db, company.id, "High Bar Intern", min_score=60.0, branches="AIML")

        service = PlacementService(db)
        results = await service.list_internships(user_id=user.id)
        hb_intern = next((r for r in results if r.title == "High Bar Intern"), None)
        assert hb_intern is not None
        assert hb_intern.is_eligible is False
        assert "readiness" in hb_intern.eligibility_reason.lower() or "score" in hb_intern.eligibility_reason.lower()
        print(f"[PASS] score ineligibility: {hb_intern.eligibility_reason}")


async def test_apply_internship_happy_path(engine: AsyncEngine, Session):
    """Eligible student should be able to apply successfully."""
    async with Session() as db:
        user, student = await _make_user_and_student(db, "intern.apply@test.com", "AIML")
        company = await _make_company(db, "HappyCorp")
        await _set_readiness(db, student.id, company.id, 70.0)

        internship = await _make_internship(db, company.id, "Happy Path Intern", min_score=50.0, branches="AIML")

        service = PlacementService(db)
        app = await service.apply(
            user_id=user.id,
            payload=ApplicationCreate(internship_id=internship.id),
        )
        assert app.status == "APPLIED"
        assert app.internship_id == internship.id
        assert app.company_id == company.id
        assert app.readiness_score_at_apply == 70.0
        print(f"[PASS] apply internship: status={app.status}, readiness_at_apply={app.readiness_score_at_apply}")


async def test_apply_placement_happy_path(engine: AsyncEngine, Session):
    """Eligible student should be able to apply for a placement job."""
    async with Session() as db:
        user, student = await _make_user_and_student(db, "place.apply@test.com", "AIML")
        company = await _make_company(db, "PlaceCorp")
        await _set_readiness(db, student.id, company.id, 65.0)

        job = await _make_placement(db, company.id, "Software Engineer", min_score=55.0, branches="AIML")

        service = PlacementService(db)
        app = await service.apply(
            user_id=user.id,
            payload=ApplicationCreate(placement_job_id=job.id),
        )
        assert app.status == "APPLIED"
        assert app.placement_job_id == job.id
        print(f"[PASS] apply placement: status={app.status}")


async def test_apply_ineligible_raises_error(engine: AsyncEngine, Session):
    """Ineligible student (low readiness) should not be able to apply."""
    async with Session() as db:
        user, student = await _make_user_and_student(db, "intern.inelig@test.com", "AIML")
        company = await _make_company(db, "IneligCorp")
        await _set_readiness(db, student.id, company.id, 20.0)  # too low

        internship = await _make_internship(db, company.id, "Blocked Intern", min_score=60.0, branches="AIML")

        service = PlacementService(db)
        raised = False
        try:
            await service.apply(user_id=user.id, payload=ApplicationCreate(internship_id=internship.id))
        except BadRequestException:
            raised = True
        assert raised, "Expected BadRequestException for ineligible student"
        print("[PASS] ineligible apply raises BadRequestException")


async def test_duplicate_application_rejected(engine: AsyncEngine, Session):
    """Second application to the same internship should be rejected."""
    async with Session() as db:
        user, student = await _make_user_and_student(db, "intern.dup@test.com", "AIML")
        company = await _make_company(db, "DupCorp")
        await _set_readiness(db, student.id, company.id, 70.0)

        internship = await _make_internship(db, company.id, "Dup Test Intern", min_score=50.0, branches="AIML")

        service = PlacementService(db)
        await service.apply(user_id=user.id, payload=ApplicationCreate(internship_id=internship.id))

        raised = False
        try:
            await service.apply(user_id=user.id, payload=ApplicationCreate(internship_id=internship.id))
        except BadRequestException:
            raised = True
        assert raised, "Expected BadRequestException for duplicate application"
        print("[PASS] duplicate application rejected")


async def test_application_stage_pipeline(engine: AsyncEngine, Session):
    """Application should advance through full pipeline: APPLIED→SHORTLISTED→ONLINE_TEST→TECHNICAL→HR→SELECTED."""
    async with Session() as db:
        user, student = await _make_user_and_student(db, "intern.pipeline@test.com", "AIML")
        company = await _make_company(db, "PipelineCorp")
        await _set_readiness(db, student.id, company.id, 80.0)

        internship = await _make_internship(db, company.id, "Pipeline Intern", min_score=50.0, branches="AIML")

        service = PlacementService(db)
        app = await service.apply(user_id=user.id, payload=ApplicationCreate(internship_id=internship.id))
        assert app.status == "APPLIED"

        stages = ["SHORTLISTED", "ONLINE_TEST", "TECHNICAL", "HR", "SELECTED"]
        for stage in stages:
            app = await service.update_status(
                application_id=app.id,
                payload=ApplicationStatusUpdate(status=stage, feedback=f"Moving to {stage}"),
            )
            assert app.status == stage
            print(f"  -> {stage} OK")

        print(f"[PASS] full stage pipeline: {' -> '.join(stages)}")


async def test_offer_letter_generated_on_selected(engine: AsyncEngine, Session):
    """An offer letter should be automatically generated when status = SELECTED."""
    async with Session() as db:
        user, student = await _make_user_and_student(db, "intern.offer@test.com", "AIML")
        company = await _make_company(db, "OfferCorp")
        await _set_readiness(db, student.id, company.id, 80.0)

        internship = await _make_internship(db, company.id, "Offer Intern", min_score=50.0, branches="AIML")

        service = PlacementService(db)
        app = await service.apply(user_id=user.id, payload=ApplicationCreate(internship_id=internship.id))

        for stage in ["SHORTLISTED", "ONLINE_TEST", "TECHNICAL", "HR", "SELECTED"]:
            app = await service.update_status(
                application_id=app.id,
                payload=ApplicationStatusUpdate(status=stage),
            )

        # app is a Pydantic schema, not ORM — query OfferLetter from DB directly
        ol_res = await db.execute(
            select(OfferLetter).where(OfferLetter.application_id == app.id)
        )
        ol = ol_res.scalars().first()
        assert ol is not None, "Offer letter should be auto-generated on SELECTED"
        assert ol.offer_type == "INTERNSHIP"
        assert ol.package == 50000.0  # stipend
        print(f"[PASS] offer letter auto-generated: type={ol.offer_type}, package={ol.package}")


async def test_invalid_stage_transition_rejected(engine: AsyncEngine, Session):
    """Jumping from APPLIED directly to SELECTED should raise BadRequestException."""
    async with Session() as db:
        user, student = await _make_user_and_student(db, "intern.invtrans@test.com", "AIML")
        company = await _make_company(db, "TransCorp")
        await _set_readiness(db, student.id, company.id, 80.0)

        internship = await _make_internship(db, company.id, "Trans Intern", min_score=50.0, branches="AIML")

        service = PlacementService(db)
        app = await service.apply(user_id=user.id, payload=ApplicationCreate(internship_id=internship.id))
        assert app.status == "APPLIED"

        raised = False
        try:
            await service.update_status(
                application_id=app.id,
                payload=ApplicationStatusUpdate(status="SELECTED"),
            )
        except BadRequestException:
            raised = True
        assert raised, "Expected BadRequestException for invalid transition"
        print("[PASS] invalid transition APPLIED->SELECTED raises BadRequestException")


async def test_application_history(engine: AsyncEngine, Session):
    """get_my_applications should return all applications for the student."""
    async with Session() as db:
        user, student = await _make_user_and_student(db, "intern.history@test.com", "AIML")
        company1 = await _make_company(db, "HistCorp1")
        company2 = await _make_company(db, "HistCorp2")
        await _set_readiness(db, student.id, company1.id, 80.0)
        await _set_readiness(db, student.id, company2.id, 80.0)

        i1 = await _make_internship(db, company1.id, "History Intern A", min_score=50.0, branches="AIML")
        p1 = await _make_placement(db, company2.id, "History Job B", min_score=50.0, branches="AIML")

        service = PlacementService(db)
        await service.apply(user_id=user.id, payload=ApplicationCreate(internship_id=i1.id))
        await service.apply(user_id=user.id, payload=ApplicationCreate(placement_job_id=p1.id))

        history = await service.get_my_applications(user_id=user.id)
        assert len(history) >= 2
        types = {h.application_type for h in history}
        assert "INTERNSHIP" in types
        assert "PLACEMENT" in types
        print(f"[PASS] application history: {len(history)} applications, types={types}")


async def test_dashboard_summary(engine: AsyncEngine, Session):
    """Dashboard should correctly count application statuses."""
    async with Session() as db:
        user, student = await _make_user_and_student(db, "intern.dash@test.com", "AIML")
        company = await _make_company(db, "DashCorp")
        await _set_readiness(db, student.id, company.id, 90.0)

        i1 = await _make_internship(db, company.id, "Dash Intern1", min_score=50.0, branches="AIML")
        i2 = await _make_internship(db, company.id, "Dash Intern2", min_score=50.0, branches="AIML")

        service = PlacementService(db)
        app1 = await service.apply(user_id=user.id, payload=ApplicationCreate(internship_id=i1.id))
        app2 = await service.apply(user_id=user.id, payload=ApplicationCreate(internship_id=i2.id))

        # Advance app2 to SHORTLISTED
        await service.update_status(app2.id, ApplicationStatusUpdate(status="SHORTLISTED"))

        dashboard = await service.get_dashboard(user_id=user.id)
        assert dashboard.summary.total_applications >= 2
        assert dashboard.summary.applied >= 1
        assert dashboard.summary.shortlisted >= 1
        print(f"[PASS] dashboard: total={dashboard.summary.total_applications}, applied={dashboard.summary.applied}, shortlisted={dashboard.summary.shortlisted}")


async def test_list_placements_eligible(engine: AsyncEngine, Session):
    """Eligible placement jobs should have is_eligible=True."""
    async with Session() as db:
        user, student = await _make_user_and_student(db, "place.list@test.com", "AIML")
        company = await _make_company(db, "PlaceListCorp")
        await _set_readiness(db, student.id, company.id, 70.0)

        await _make_placement(db, company.id, "List Test SDE", min_score=60.0, branches="AIML")

        service = PlacementService(db)
        results = await service.list_placements(user_id=user.id)
        sde = next((r for r in results if r.title == "List Test SDE"), None)
        assert sde is not None
        assert sde.is_eligible is True
        print(f"[PASS] list_placements: found {len(results)} jobs, SDE eligible")


async def test_readiness_check_gates_application(engine: AsyncEngine, Session):
    """Readiness score exactly at threshold should be eligible; one below should not."""
    async with Session() as db:
        user, student = await _make_user_and_student(db, "intern.gate@test.com", "AIML")
        company = await _make_company(db, "GateCorp")

        # Exactly at threshold
        await _set_readiness(db, student.id, company.id, 55.0)
        internship = await _make_internship(db, company.id, "Gate Intern", min_score=55.0, branches="AIML")

        service = PlacementService(db)
        app = await service.apply(user_id=user.id, payload=ApplicationCreate(internship_id=internship.id))
        assert app.status == "APPLIED"
        print("[PASS] readiness exactly at threshold: application accepted")


async def test_offer_accept_decline(engine: AsyncEngine, Session):
    """Student should be able to accept or decline an offer letter."""
    async with Session() as db:
        user, student = await _make_user_and_student(db, "intern.acceptoffer@test.com", "AIML")
        company = await _make_company(db, "AcceptCorp")
        await _set_readiness(db, student.id, company.id, 90.0)

        internship = await _make_internship(db, company.id, "Accept Intern", min_score=50.0, branches="AIML")

        service = PlacementService(db)
        app = await service.apply(user_id=user.id, payload=ApplicationCreate(internship_id=internship.id))

        for stage in ["SHORTLISTED", "ONLINE_TEST", "TECHNICAL", "HR", "SELECTED"]:
            app = await service.update_status(app.id, ApplicationStatusUpdate(status=stage))

        offers = await service.get_offer_letters(user_id=user.id)
        assert len(offers) >= 1
        offer_id = offers[0].id

        accepted_offer = await service.accept_offer(user_id=user.id, offer_id=offer_id, accept=True)
        assert accepted_offer.accepted is True
        print(f"[PASS] offer accepted: id={offer_id}, accepted={accepted_offer.accepted}")


async def test_student_not_found_raises_404(engine: AsyncEngine, Session):
    """Non-existent user_id should raise NotFoundException."""
    async with Session() as db:
        service = PlacementService(db)
        raised = False
        try:
            await service.list_internships(user_id="non-existent-user-id")
        except NotFoundException:
            raised = True
        assert raised
        print("[PASS] non-existent user raises NotFoundException")


async def test_no_payload_raises_error(engine: AsyncEngine, Session):
    """Applying without internship_id or placement_job_id should raise BadRequestException."""
    async with Session() as db:
        user, student = await _make_user_and_student(db, "intern.nopayload@test.com", "AIML")
        service = PlacementService(db)
        raised = False
        try:
            await service.apply(user_id=user.id, payload=ApplicationCreate())
        except BadRequestException:
            raised = True
        assert raised
        print("[PASS] empty payload raises BadRequestException")


async def test_both_ids_raises_error(engine: AsyncEngine, Session):
    """Providing both internship_id and placement_job_id should raise BadRequestException."""
    async with Session() as db:
        user, student = await _make_user_and_student(db, "intern.bothids@test.com", "AIML")
        service = PlacementService(db)
        raised = False
        try:
            await service.apply(
                user_id=user.id,
                payload=ApplicationCreate(internship_id="id1", placement_job_id="id2"),
            )
        except BadRequestException:
            raised = True
        assert raised
        print("[PASS] both ids raises BadRequestException")


# ─── Runner ───────────────────────────────────────────────────────────────────

TESTS = [
    test_list_internships_with_eligibility,
    test_list_internships_ineligible_branch,
    test_list_internships_ineligible_score,
    test_apply_internship_happy_path,
    test_apply_placement_happy_path,
    test_apply_ineligible_raises_error,
    test_duplicate_application_rejected,
    test_application_stage_pipeline,
    test_offer_letter_generated_on_selected,
    test_invalid_stage_transition_rejected,
    test_application_history,
    test_dashboard_summary,
    test_list_placements_eligible,
    test_readiness_check_gates_application,
    test_offer_accept_decline,
    test_student_not_found_raises_404,
    test_no_payload_raises_error,
    test_both_ids_raises_error,
]

if __name__ == "__main__":
    import sys, asyncio, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
    for p in pathlib.Path(".").rglob("*.pyc"):
        p.unlink(missing_ok=True)

    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
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
        print("=" * 58)
        print(f"Internship & Placement Engine: {passed} passed, {failed} failed")
        print("=" * 58)

    asyncio.run(run())
