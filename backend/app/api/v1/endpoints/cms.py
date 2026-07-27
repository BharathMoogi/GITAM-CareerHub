"""
Enterprise Admin CMS — REST API Endpoints.

Routes:
  GET  /admin/audit-logs          → View audit log history
  POST /admin/approvals           → Submit content approval request
  PATCH /admin/approvals/{id}     → Approve / Reject approval request
  GET  /admin/approvals/pending   → List pending approval queue
  GET  /admin/versions            → View content version history
  POST /admin/soft-delete         → Soft delete content item
  POST /admin/restore             → Restore soft-deleted content item
  POST /admin/import/csv          → Bulk CSV Import engine
  GET  /admin/export/excel        → Excel Export dataset generator
  GET  /admin/search              → Global search across all CMS modules
  POST /admin/blogs               → Create blog post
  POST /admin/events              → Create campus event
  POST /admin/resources           → Create career resource
"""
import logging
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.services.cms_service import CmsService
from app.schemas.cms import (
    AuditLogItem, SubmitApprovalRequest, ReviewApprovalRequest, ApprovalResponse,
    ContentVersionItem, SoftDeleteRequest, RestoreRequest, SoftDeleteResponse,
    BulkImportCsvRequest, BulkImportResponse, ExcelExportResponse,
    SearchResponse, CreateBlogRequest, CreateEventRequest, CreateResourceRequest
)

logger = logging.getLogger("app.api.cms")
router = APIRouter()

ALLOWED_CMS_ROLES = ["SUPER_ADMIN", "COLLEGE_ADMIN", "DEPARTMENT_ADMIN", "FACULTY", "PLACEMENT_OFFICER", "MODERATOR"]


# ── 1. Audit Logs ─────────────────────────────────────────────────────────────

@router.get(
    "/admin/audit-logs",
    response_model=List[AuditLogItem],
    summary="View System Audit Logs",
    description="Returns audit trail of administrative actions across all modules.",
)
async def get_audit_logs(
    resource_type: Optional[str] = Query(None, description="Resource type filter (e.g. STUDENT, COURSE)"),
    action: Optional[str] = Query(None, description="Action filter (e.g. CREATE, DELETE)"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CmsService(db)
    await service.verify_rbac(user_id=current_user.id, allowed_roles=ALLOWED_CMS_ROLES)
    results = await service.get_audit_logs(resource_type=resource_type, action=action, limit=limit)
    return [AuditLogItem(**log) for log in results]


# ── 2. Approval Workflows ─────────────────────────────────────────────────────

@router.post(
    "/admin/approvals",
    response_model=ApprovalResponse,
    status_code=201,
    summary="Submit Approval Request",
    description="Submits a content or entity publishing request for administrative review.",
)
async def submit_approval(
    request: SubmitApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CmsService(db)
    await service.verify_rbac(user_id=current_user.id, allowed_roles=ALLOWED_CMS_ROLES)
    result = await service.submit_approval_request(
        requester_id=current_user.id,
        resource_type=request.resource_type,
        resource_id=request.resource_id,
        action_type=request.action_type,
        notes=request.notes,
    )
    return ApprovalResponse(**result)


@router.patch(
    "/admin/approvals/{request_id}",
    response_model=ApprovalResponse,
    summary="Approve or Reject Request",
    description="Approve or reject a pending approval request (Admin/Moderator role required).",
)
async def review_approval(
    request_id: str = Path(..., description="Approval Request ID"),
    request: ReviewApprovalRequest = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CmsService(db)
    await service.verify_rbac(user_id=current_user.id, allowed_roles=["SUPER_ADMIN", "COLLEGE_ADMIN", "DEPARTMENT_ADMIN", "MODERATOR"])
    result = await service.review_approval_request(
        approver_id=current_user.id,
        request_id=request_id,
        status=request.status,
        notes=request.notes,
    )
    return ApprovalResponse(**result)


@router.get(
    "/admin/approvals/pending",
    response_model=List[Dict[str, Any]],
    summary="List Pending Approvals",
)
async def get_pending_approvals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CmsService(db)
    await service.verify_rbac(user_id=current_user.id, allowed_roles=ALLOWED_CMS_ROLES)
    return await service.get_pending_approvals()


# ── 3. Content Version History ────────────────────────────────────────────────

@router.get(
    "/admin/versions",
    response_model=List[ContentVersionItem],
    summary="View Content Version History",
    description="Returns snapshot history for a given content resource.",
)
async def get_version_history(
    resource_type: str = Query(..., description="Resource type (e.g. BLOG, COURSE)"),
    resource_id: str = Query(..., description="Resource ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CmsService(db)
    await service.verify_rbac(user_id=current_user.id, allowed_roles=ALLOWED_CMS_ROLES)
    results = await service.get_version_history(resource_type=resource_type, resource_id=resource_id)
    return [ContentVersionItem(**v) for v in results]


# ── 4. Soft Delete & Restore ──────────────────────────────────────────────────

@router.post(
    "/admin/soft-delete",
    response_model=SoftDeleteResponse,
    summary="Soft Delete Content",
)
async def soft_delete(
    request: SoftDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CmsService(db)
    await service.verify_rbac(user_id=current_user.id, allowed_roles=ALLOWED_CMS_ROLES)
    result = await service.soft_delete_resource(
        resource_type=request.resource_type,
        resource_id=request.resource_id,
        user_id=current_user.id,
    )
    return SoftDeleteResponse(**result)


@router.post(
    "/admin/restore",
    response_model=SoftDeleteResponse,
    summary="Restore Soft-Deleted Content",
)
async def restore_content(
    request: RestoreRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CmsService(db)
    await service.verify_rbac(user_id=current_user.id, allowed_roles=ALLOWED_CMS_ROLES)
    result = await service.restore_resource(
        resource_type=request.resource_type,
        resource_id=request.resource_id,
        user_id=current_user.id,
    )
    return SoftDeleteResponse(**result)


# ── 5. Bulk CSV Import & Excel Export ─────────────────────────────────────────

@router.post(
    "/admin/import/csv",
    response_model=BulkImportResponse,
    summary="Bulk CSV Import",
    description="Imports structured rows from CSV into the target module (Students, Companies, Courses, Projects).",
)
async def bulk_import_csv(
    request: BulkImportCsvRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CmsService(db)
    await service.verify_rbac(user_id=current_user.id, allowed_roles=["SUPER_ADMIN", "COLLEGE_ADMIN", "DEPARTMENT_ADMIN", "PLACEMENT_OFFICER"])
    result = await service.bulk_import_csv(
        module_name=request.module_name,
        csv_content=request.csv_content,
        user_id=current_user.id,
    )
    return BulkImportResponse(**result)


@router.get(
    "/admin/export/excel",
    response_model=ExcelExportResponse,
    summary="Export Module Dataset to Excel",
    description="Generates downloadable Excel XLSX structured data table payload for any module.",
)
async def export_excel(
    module_name: str = Query(..., description="Module name (e.g. STUDENTS, PLACEMENTS, COMPANIES)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CmsService(db)
    await service.verify_rbac(user_id=current_user.id, allowed_roles=ALLOWED_CMS_ROLES)
    result = await service.export_excel(module_name=module_name, user_id=current_user.id)
    return ExcelExportResponse(**result)


# ── 6. Global Search ──────────────────────────────────────────────────────────

@router.get(
    "/admin/search",
    response_model=SearchResponse,
    summary="Cross-Module Global Search",
    description="Searches across all CMS modules (Students, Companies, Courses, Projects, Blogs, Events, Resources).",
)
async def global_search(
    q: str = Query(..., min_length=1, description="Search query string"),
    module: Optional[str] = Query(None, description="Optional module filter (e.g. BLOG, EVENT)"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CmsService(db)
    await service.verify_rbac(user_id=current_user.id, allowed_roles=ALLOWED_CMS_ROLES)
    result = await service.global_search(query=q, module=module, limit=limit)
    return SearchResponse(**result)


# ── 7. Blogs, Events, Resources CRUD ─────────────────────────────────────────

@router.post(
    "/admin/blogs",
    status_code=201,
    summary="Create Blog Post",
)
async def create_blog(
    request: CreateBlogRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CmsService(db)
    await service.verify_rbac(user_id=current_user.id, allowed_roles=ALLOWED_CMS_ROLES)
    return await service.create_blog(
        author_id=current_user.id,
        title=request.title,
        content=request.content,
        category=request.category,
    )


@router.post(
    "/admin/events",
    status_code=201,
    summary="Create Campus Event",
)
async def create_event(
    request: CreateEventRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CmsService(db)
    await service.verify_rbac(user_id=current_user.id, allowed_roles=ALLOWED_CMS_ROLES)
    return await service.create_event(
        title=request.title,
        description=request.description,
        event_date=request.event_date,
        event_type=request.event_type,
        user_id=current_user.id,
    )


@router.post(
    "/admin/resources",
    status_code=201,
    summary="Create Career Resource",
)
async def create_resource(
    request: CreateResourceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CmsService(db)
    await service.verify_rbac(user_id=current_user.id, allowed_roles=ALLOWED_CMS_ROLES)
    return await service.create_resource(
        title=request.title,
        url=request.url,
        resource_type=request.resource_type,
        category=request.category,
        user_id=current_user.id,
    )
