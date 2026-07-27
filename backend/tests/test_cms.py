"""
Tests for the Enterprise Admin CMS.

Covers:
  1. RBAC Verification (SUPER_ADMIN, COLLEGE_ADMIN, FACULTY allowed vs STUDENT forbidden)
  2. Audit Log creation & retrieval
  3. Approval Workflow (submission, review, pending listing)
  4. Content Version Snapshots
  5. Soft Delete & Restore operations
  6. Bulk CSV Import and Excel Export engine
  7. Cross-Module Global Search
  8. Content CRUD (Blogs, Events, Resources)
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
from app.models.cms import AuditLog, ApprovalRequest, ContentVersion, CmsBlog, CmsEvent, CmsResource
from app.services.cms_service import CmsService
from app.core.exceptions import ForbiddenException, NotFoundException, BadRequestException


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _make_user(db, email="admin.cms@gitam.edu", role="SUPER_ADMIN"):
    user = User(email=email, hashed_password="hash", is_active=True, role=role)
    db.add(user); await db.commit(); await db.refresh(user)
    return user


# ─── Tests ────────────────────────────────────────────────────────────────────

async def test_rbac_verification(engine, Session):
    """SUPER_ADMIN and allowed roles should pass; STUDENT role should raise ForbiddenException."""
    async with Session() as db:
        super_admin = await _make_user(db, "super.admin@gitam.edu", "SUPER_ADMIN")
        student = await _make_user(db, "stu.rbac@gitam.edu", "STUDENT")

        service = CmsService(db)
        u1 = await service.verify_rbac(super_admin.id, ["COLLEGE_ADMIN"])
        assert u1.id == super_admin.id

        raised = False
        try:
            await service.verify_rbac(student.id, ["FACULTY", "COLLEGE_ADMIN"])
        except ForbiddenException:
            raised = True
        assert raised
        print("[PASS] RBAC verification: SUPER_ADMIN allowed, STUDENT forbidden")


async def test_audit_logging(engine, Session):
    """log_action should create AuditLog entry with IP address and JSON delta."""
    async with Session() as db:
        user = await _make_user(db, "audit.cms@gitam.edu", "COLLEGE_ADMIN")
        service = CmsService(db)

        log = await service.log_action(
            user_id=user.id,
            action="UPDATE",
            resource_type="COURSE",
            resource_id="crs-123",
            changes_json='{"title": "Updated Course Title"}',
            ip_address="192.168.1.100",
        )
        assert log.id
        assert log.action == "UPDATE"
        assert log.resource_type == "COURSE"

        logs = await service.get_audit_logs(resource_type="COURSE")
        assert len(logs) >= 1
        assert logs[0]["changes"]["title"] == "Updated Course Title"
        print(f"[PASS] audit log recorded: action={log.action}, resource={log.resource_type}")


async def test_approval_workflow(engine, Session):
    """Approval request submission, review, and pending listing."""
    async with Session() as db:
        requester = await _make_user(db, "req.cms@gitam.edu", "FACULTY")
        approver = await _make_user(db, "app.cms@gitam.edu", "SUPER_ADMIN")
        service = CmsService(db)

        # Submit request
        sub = await service.submit_approval_request(
            requester_id=requester.id,
            resource_type="BLOG",
            resource_id="blog-555",
            action_type="PUBLISH",
            notes="Please approve new AI article",
        )
        assert sub["status"] == "PENDING"

        # Check pending list
        pending = await service.get_pending_approvals()
        assert len(pending) >= 1

        # Review approval
        rev = await service.review_approval_request(
            approver_id=approver.id,
            request_id=sub["id"],
            status="APPROVED",
            notes="Approved for campus publishing",
        )
        assert rev["status"] == "APPROVED"
        print("[PASS] approval workflow submission & approval verified")


async def test_version_history(engine, Session):
    """save_version_snapshot and get_version_history."""
    async with Session() as db:
        user = await _make_user(db, "ver.cms@gitam.edu", "SUPER_ADMIN")
        service = CmsService(db)

        v1 = await service.save_version_snapshot("PROJECT", "proj-999", {"title": "Version 1 Title"}, user.id)
        assert v1["version_number"] == 1

        v2 = await service.save_version_snapshot("PROJECT", "proj-999", {"title": "Version 2 Title"}, user.id)
        assert v2["version_number"] == 2

        history = await service.get_version_history("PROJECT", "proj-999")
        assert len(history) == 2
        assert history[0]["version_number"] == 2
        print(f"[PASS] content version history: {len(history)} snapshots recorded")


async def test_soft_delete_and_restore(engine, Session):
    """soft_delete_resource and restore_resource."""
    async with Session() as db:
        user = await _make_user(db, "sd.cms@gitam.edu", "SUPER_ADMIN")
        service = CmsService(db)

        blog = await service.create_blog(user.id, "Soft Delete Test Blog", "Content body here")
        blog_id = blog["id"]

        sd = await service.soft_delete_resource("BLOG", blog_id, user.id)
        assert sd["status"] == "SOFT_DELETED"

        rst = await service.restore_resource("BLOG", blog_id, user.id)
        assert rst["status"] == "RESTORED"
        print("[PASS] soft delete & restore operations verified")


async def test_bulk_csv_import_and_excel_export(engine, Session):
    """bulk_import_csv and export_excel."""
    async with Session() as db:
        user = await _make_user(db, "import.cms@gitam.edu", "SUPER_ADMIN")
        service = CmsService(db)

        csv_str = "name,email,branch\nJohn Doe,john@gitam.edu,AIML\nJane Smith,jane@gitam.edu,ECE"
        imp = await service.bulk_import_csv("STUDENTS", csv_str, user.id)
        assert imp["total_rows_processed"] == 2
        assert imp["status"] == "SUCCESS"

        exp = await service.export_excel("STUDENTS", user.id)
        assert exp["format"] == "EXCEL_XLSX_COMPLIANT_JSON"
        assert len(exp["columns"]) > 0
        print(f"[PASS] bulk CSV import ({imp['total_rows_processed']} rows) & Excel export verified")


async def test_global_search_and_crud(engine, Session):
    """create_blog, create_event, create_resource, and global_search."""
    async with Session() as db:
        user = await _make_user(db, "crud.cms@gitam.edu", "SUPER_ADMIN")
        service = CmsService(db)

        blog = await service.create_blog(user.id, "Machine Learning Trends 2026", "ML & AI insights article")
        evt = await service.create_event("GITAM AI Hackathon 2026", "24-hour coding event", datetime.now(timezone.utc), "HACKATHON", user.id)
        rec = await service.create_resource("DSA Complete Cheatsheet", "https://resources.gitam.edu/dsa.pdf", "PDF", "INTERVIEW_PREP", user.id)

        search = await service.global_search("Machine Learning")
        assert search["total_matches"] >= 1
        assert search["results"][0]["title"] == "Machine Learning Trends 2026"
        print(f"[PASS] global search matched: '{search['results'][0]['title']}'")


# ─── Runner ───────────────────────────────────────────────────────────────────

TESTS = [
    test_rbac_verification,
    test_audit_logging,
    test_approval_workflow,
    test_version_history,
    test_soft_delete_and_restore,
    test_bulk_csv_import_and_excel_export,
    test_global_search_and_crud,
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
        print(f"Enterprise Admin CMS: {passed} passed, {failed} failed")
        print("=" * 60)

    asyncio.run(run())
