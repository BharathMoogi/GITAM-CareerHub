"""
Internship & Placement Engine — Pydantic Schemas.
"""
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field


# ─── Internship Schemas ───────────────────────────────────────────────────────

class InternshipListRead(BaseModel):
    id: str
    company_id: str
    company_name: str
    company_logo: Optional[str] = None
    title: str
    internship_type: str
    mode: str
    stipend: Optional[int] = None
    duration: Optional[str] = None
    location: Optional[str] = None
    openings: int
    application_start: Optional[date] = None
    application_end: Optional[date] = None
    minimum_readiness_score: float
    status: str
    is_eligible: bool
    eligibility_reason: Optional[str] = None

    class Config:
        from_attributes = True


class InternshipDetailRead(InternshipListRead):
    job_role_id: Optional[str] = None
    job_role_title: Optional[str] = None
    description: Optional[str] = None
    eligibility_criteria: Optional[str] = None
    minimum_cgpa: Optional[float] = None
    allowed_branches: Optional[str] = None
    official_apply_link: Optional[str] = None
    student_readiness_score: Optional[float] = None


# ─── Placement Schemas ────────────────────────────────────────────────────────

class PlacementJobListRead(BaseModel):
    id: str
    company_id: str
    company_name: str
    company_logo: Optional[str] = None
    title: str
    package_min: Optional[float] = None
    package_max: Optional[float] = None
    location: Optional[str] = None
    openings: int
    deadline: Optional[date] = None
    minimum_readiness_score: float
    status: str
    is_eligible: bool
    eligibility_reason: Optional[str] = None

    class Config:
        from_attributes = True


class PlacementJobDetailRead(PlacementJobListRead):
    job_role_id: Optional[str] = None
    job_role_title: Optional[str] = None
    description: Optional[str] = None
    bond: Optional[str] = None
    eligibility_criteria: Optional[str] = None
    minimum_cgpa: Optional[float] = None
    allowed_branches: Optional[str] = None
    official_apply_link: Optional[str] = None
    student_readiness_score: Optional[float] = None


# ─── Application Schemas ──────────────────────────────────────────────────────

class ApplicationCreate(BaseModel):
    internship_id: Optional[str] = Field(None, description="Internship ID to apply for")
    placement_job_id: Optional[str] = Field(None, description="Placement Job ID to apply for")


class ApplicationStatusUpdate(BaseModel):
    status: str = Field(..., description="New application status (SHORTLISTED/ONLINE_TEST/TECHNICAL/HR/SELECTED/REJECTED)")
    feedback: Optional[str] = Field(None, description="Feedback notes for the student")


class InterviewScheduleRead(BaseModel):
    id: str
    round_name: str
    scheduled_date: Optional[datetime] = None
    meeting_link: Optional[str] = None
    venue: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


class OfferLetterRead(BaseModel):
    id: str
    company_name: str
    offer_type: str
    package: Optional[float] = None
    joining_date: Optional[date] = None
    offer_letter_url: Optional[str] = None
    accepted: Optional[bool] = None
    issued_at: datetime

    class Config:
        from_attributes = True


class ApplicationRead(BaseModel):
    id: str
    company_id: str
    company_name: str
    company_logo: Optional[str] = None
    internship_id: Optional[str] = None
    internship_title: Optional[str] = None
    placement_job_id: Optional[str] = None
    placement_job_title: Optional[str] = None
    application_type: str  # "INTERNSHIP" or "PLACEMENT"
    status: str
    application_date: datetime
    last_updated: datetime
    feedback: Optional[str] = None
    readiness_score_at_apply: Optional[float] = None
    interview_schedules: List[InterviewScheduleRead] = []
    offer_letter: Optional[OfferLetterRead] = None

    class Config:
        from_attributes = True


class ApplicationSummary(BaseModel):
    total_applications: int
    saved: int
    applied: int
    shortlisted: int
    in_progress: int  # ONLINE_TEST + TECHNICAL + HR
    selected: int
    rejected: int
    offers_received: int
    offers_accepted: int


class PlacementDashboard(BaseModel):
    summary: ApplicationSummary
    recent_applications: List[ApplicationRead]
    active_internships: List[InternshipListRead]
    active_placements: List[PlacementJobListRead]
