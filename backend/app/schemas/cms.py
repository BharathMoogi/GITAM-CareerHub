"""
Pydantic schemas for Enterprise Admin CMS API.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── Requests ──────────────────────────────────────────────────────────────────

class SubmitApprovalRequest(BaseModel):
    resource_type: str = Field(..., description="BLOG / COURSE / PROJECT / COMPANY / PLACEMENT etc.")
    resource_id: str
    action_type: str = Field(default="PUBLISH", description="PUBLISH / DELETE / OVERWRITE")
    notes: Optional[str] = None


class ReviewApprovalRequest(BaseModel):
    status: str = Field(..., description="APPROVED or REJECTED")
    notes: Optional[str] = None


class SoftDeleteRequest(BaseModel):
    resource_type: str = Field(..., description="BLOG / EVENT / RESOURCE")
    resource_id: str


class RestoreRequest(BaseModel):
    resource_type: str = Field(..., description="BLOG / EVENT / RESOURCE")
    resource_id: str


class BulkImportCsvRequest(BaseModel):
    module_name: str = Field(..., description="STUDENTS / COURSES / PROJECTS / COMPANIES / PLACEMENTS")
    csv_content: str = Field(..., min_length=1, description="Raw CSV string content")


class CreateBlogRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    category: str = Field(default="CAREER_GUIDANCE")


class CreateEventRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    event_date: datetime
    event_type: str = Field(default="WEBINAR")


class CreateResourceRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., min_length=1, max_length=500)
    resource_type: str = Field(default="PDF")
    category: str = Field(default="INTERVIEW_PREP")


# ── Responses ─────────────────────────────────────────────────────────────────

class AuditLogItem(BaseModel):
    id: str
    user_id: str
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    changes: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    timestamp: str


class ApprovalResponse(BaseModel):
    id: str
    resource_type: str
    resource_id: str
    status: str
    message: str


class ContentVersionItem(BaseModel):
    id: str
    version_number: int
    created_by_id: str
    created_at: str
    snapshot: Dict[str, Any]


class SoftDeleteResponse(BaseModel):
    resource_type: str
    resource_id: str
    status: str


class BulkImportResponse(BaseModel):
    module_name: str
    total_rows_processed: int
    status: str
    sample_imported_keys: List[str]


class ExcelExportResponse(BaseModel):
    module_name: str
    format: str
    columns: List[str]
    rows_count: int
    download_url: str


class SearchResultItem(BaseModel):
    type: str
    id: str
    title: str
    subtitle: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    total_matches: int
    results: List[SearchResultItem]
