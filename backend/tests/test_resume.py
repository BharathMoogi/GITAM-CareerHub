"""
Tests for the Resume Intelligence Engine.

Covers:
  1. Resume profile creation and headline/summary updates
  2. Experience, hackathon, publication, and patent additions
  3. Structured ATS Resume JSON and PDF metadata generation
  4. Live ATS, Resume, and Portfolio score calculations with missing keyword analysis
  5. AI Resume Review, STAR bullet improvements, and project bullet generator
  6. Personal Portfolio Website JSON generation & AI Portfolio review
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
from app.services.resume_service import ResumeService
from app.core.exceptions import NotFoundException


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _make_user_student(db, email="resume.test@gitam.edu", branch_code="AIML"):
    import uuid
    b_res = await db.execute(select(Branch).where(Branch.code == branch_code))
    b = b_res.scalars().first()
    if not b:
        b = Branch(code=branch_code, name=f"{branch_code} Dept", description="Test")
        db.add(b); await db.commit(); await db.refresh(b)

    r_res = await db.execute(select(TargetRole))
    role = r_res.scalars().first()
    if not role:
        role = TargetRole(title="AI Engineer", description="Test role")
        db.add(role); await db.commit(); await db.refresh(role)

    user = User(email=email, hashed_password="hash", is_active=True, role="STUDENT")
    db.add(user); await db.flush()

    student = Student(
        user_id=user.id, full_name="Resume Test Student", email=email,
        roll_number=f"R{uuid.uuid4().hex[:8].upper()}",
        branch_id=b.id, target_role_id=role.id,
        current_year=3, semester=5, is_active=True,
    )
    db.add(student); await db.commit()
    await db.refresh(user); await db.refresh(student)
    return user, student


# ─── Tests ────────────────────────────────────────────────────────────────────

async def test_get_or_create_resume(engine, Session):
    """Initial call to get_or_create_resume should create a default resume profile."""
    async with Session() as db:
        user, student = await _make_user_student(db, "res.init@gitam.edu")
        service = ResumeService(db)
        data = await service.get_or_create_resume(user.id)

        assert data["id"]
        assert data["student_id"] == student.id
        assert "Aspiring AI Engineer" in data["headline"]
        assert "experiences" in data
        print(f"[PASS] resume profile created: {data['headline']}")


async def test_update_resume_header(engine, Session):
    """update_resume_header should update headline and summary text."""
    async with Session() as db:
        user, _ = await _make_user_student(db, "res.update@gitam.edu")
        service = ResumeService(db)
        data = await service.update_resume_header(
            user_id=user.id,
            headline="Senior AI Developer",
            summary="Passionate AI systems engineer with extensive hands-on experience in MLOps and LLM integration.",
        )
        assert data["headline"] == "Senior AI Developer"
        assert "MLOps" in data["summary"]
        print(f"[PASS] updated headline: {data['headline']}")


async def test_add_experience_hackathon_pub_patent(engine, Session):
    """Adding work experience, hackathons, publications, and patents should persist successfully."""
    async with Session() as db:
        user, _ = await _make_user_student(db, "res.entries@gitam.edu")
        service = ResumeService(db)

        # Add experience
        exp_res = await service.add_experience(
            user_id=user.id,
            company_name="Google India",
            role_title="AI Engineering Intern",
            start_date=date(2025, 5, 1),
            end_date=date(2025, 8, 1),
            location="Bangalore",
            bullet_points=["Built deep learning pipeline with 95% accuracy."],
        )
        assert exp_res["id"]

        # Add hackathon
        hk_res = await service.add_hackathon(
            user_id=user.id,
            event_name="Smart India Hackathon",
            project_title="AI Crop Doctor",
            prize_rank="1st Place Winner",
        )
        assert hk_res["id"]

        # Add publication
        pub_res = await service.add_publication(
            user_id=user.id,
            title="Real-Time Detection of Agricultural Diseases using Neural Networks",
            journal_publisher="IEEE Transactions on AI",
            publication_date=date(2025, 6, 15),
        )
        assert pub_res["id"]

        # Add patent
        pat_res = await service.add_patent(
            user_id=user.id,
            title="System and Method for Low-Latency Neural Edge Inference",
            status="FILED",
        )
        assert pat_res["id"]

        # Verify all entries in resume serialization
        resume_data = await service.get_or_create_resume(user.id)
        assert len(resume_data["experiences"]) >= 1
        assert len(resume_data["hackathons"]) >= 1
        assert len(resume_data["publications"]) >= 1
        assert len(resume_data["patents"]) >= 1
        print("[PASS] added experience, hackathon, publication, and patent entries successfully")


async def test_generate_ats_resume_json_and_pdf_metadata(engine, Session):
    """generate_ats_resume_json should return valid ATS JSON, PDF layout metadata, and missing keywords."""
    async with Session() as db:
        user, _ = await _make_user_student(db, "ats.gen@gitam.edu")
        service = ResumeService(db)
        data = await service.generate_ats_resume_json(user.id)

        assert "header" in data["ats_resume_json"]
        assert "pdf_metadata" in data
        assert data["pdf_metadata"]["ats_parseable_status"] == "COMPLIANT_SINGLE_COLUMN"
        assert "scores" in data
        assert data["scores"]["ats_score"] >= 0.0
        assert "skill_gap_analysis" in data
        assert isinstance(data["recommended_improvements"], list)
        print(f"[PASS] generated ATS Resume JSON & PDF metadata: ATS Score={data['scores']['ats_score']}")


async def test_review_resume_ai(engine, Session):
    """review_resume_ai should return STAR bullet rewrites and project bullet generation."""
    async with Session() as db:
        user, _ = await _make_user_student(db, "ai.review@gitam.edu")
        service = ResumeService(db)
        data = await service.review_resume_ai(user_id=user.id, job_description="Looking for AI/ML Engineer with Python & PyTorch experience")

        assert "overall_feedback" in data
        assert isinstance(data["bullet_improvements"], list)
        assert len(data["bullet_improvements"]) > 0
        assert "action_verb" in data["bullet_improvements"][0]
        assert isinstance(data["generated_project_bullets"], list)
        print(f"[PASS] AI resume review: generated {len(data['bullet_improvements'])} STAR bullet improvements")


async def test_get_resume_score(engine, Session):
    """get_resume_score should return live ATS, Resume, and Portfolio scores."""
    async with Session() as db:
        user, _ = await _make_user_student(db, "score.test@gitam.edu")
        service = ResumeService(db)
        data = await service.get_resume_score(user.id)

        assert "scores" in data
        assert "ats_score" in data["scores"]
        assert "resume_score" in data["scores"]
        assert "portfolio_score" in data["scores"]
        print(f"[PASS] resume scores: ATS={data['scores']['ats_score']}, Resume={data['scores']['resume_score']}, Portfolio={data['scores']['portfolio_score']}")


async def test_portfolio_json_and_ai_review(engine, Session):
    """get_portfolio_json should generate portfolio website JSON and AI portfolio review."""
    async with Session() as db:
        user, _ = await _make_user_student(db, "portfolio.test@gitam.edu")
        service = ResumeService(db)

        p_json = await service.get_portfolio_json(user.id)
        assert "full_name" in p_json
        assert "portfolio_url_slug" in p_json
        assert p_json["theme"] == "MODERN_DARK"

        p_review = await service.review_portfolio_ai(user.id)
        assert "portfolio_score" in p_review
        assert isinstance(p_review["suggestions"], list)
        print(f"[PASS] portfolio JSON & AI review: URL slug={p_json['portfolio_url_slug']}, Score={p_review['portfolio_score']}")


# ─── Runner ───────────────────────────────────────────────────────────────────

TESTS = [
    test_get_or_create_resume,
    test_update_resume_header,
    test_add_experience_hackathon_pub_patent,
    test_generate_ats_resume_json_and_pdf_metadata,
    test_review_resume_ai,
    test_get_resume_score,
    test_portfolio_json_and_ai_review,
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
        print(f"Resume Intelligence Engine: {passed} passed, {failed} failed")
        print("=" * 60)

    asyncio.run(run())
