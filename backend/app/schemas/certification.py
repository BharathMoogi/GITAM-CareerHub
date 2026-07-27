from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


# ─── Sub-schemas ──────────────────────────────────────────────────────────────

class CertificationSkillRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    skill_id: str
    skill_name: str
    skill_category: str
    required_level: str


class CertificationPrerequisiteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    required_course_id: Optional[str] = None
    required_course_title: Optional[str] = None
    required_project_id: Optional[str] = None
    required_project_title: Optional[str] = None
    minimum_skill_score: Optional[float] = None


class CertificationExamRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    exam_name: str
    exam_duration: Optional[str] = None
    passing_score: Optional[float] = None
    exam_pattern: Optional[str] = None
    official_link: Optional[str] = None


class CertificationBenefitRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    benefit: str
    display_order: int


# ─── Certification List schema ────────────────────────────────────────────────

class CertificationListRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    provider: str
    provider_type: str
    description: Optional[str] = None
    official_url: Optional[str] = None
    difficulty: str
    estimated_hours: Optional[int] = None
    branch_id: str
    branch_name: str
    year_number: int
    semester_number: int
    certificate_type: str
    thumbnail: Optional[str] = None
    status: str

    # Student context
    is_locked: bool = False
    lock_reason: Optional[str] = None
    user_status: str = "NOT_STARTED"
    verified: bool = False

    skills: List[CertificationSkillRead] = Field(default_factory=list)


# ─── Certification Detail schema ──────────────────────────────────────────────

class CertificationDetailRead(CertificationListRead):
    prerequisites: List[CertificationPrerequisiteRead] = Field(default_factory=list)
    exams: List[CertificationExamRead] = Field(default_factory=list)
    benefits: List[CertificationBenefitRead] = Field(default_factory=list)

    certificate_url: Optional[str] = None
    verification_id: Optional[str] = None
    issue_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    score: Optional[float] = None


# ─── Student Certification Read schema ────────────────────────────────────────

class StudentCertificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    certification_id: str
    certification_title: str
    provider: str
    provider_type: str
    difficulty: str
    branch_name: str
    year_number: int
    semester_number: int
    status: str
    certificate_url: Optional[str] = None
    verification_id: Optional[str] = None
    issue_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    score: Optional[float] = None
    verified: bool = False
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# ─── Progress & Submission Request/Response schemas ──────────────────────────

class UpdateCertificationProgressRequest(BaseModel):
    status: str = Field(..., description="IN_PROGRESS or COMPLETED")


class SubmitCertificationRequest(BaseModel):
    certificate_url: str = Field(..., min_length=5, description="URL of certificate document or badge")
    verification_id: Optional[str] = Field(None, description="Unique certificate credential ID")
    score: Optional[float] = Field(None, ge=0.0, description="Exam score achieved")
    issue_date: Optional[datetime] = Field(None, description="Date of issue")
    expiry_date: Optional[datetime] = Field(None, description="Expiration date if applicable")


class CertificationProgressRead(BaseModel):
    certification_id: str
    certification_title: str
    status: str
    certificate_url: Optional[str] = None
    verification_id: Optional[str] = None
    issue_date: Optional[datetime] = None
    score: Optional[float] = None
    verified: bool = False
    skills_updated: List[dict] = Field(default_factory=list)
    roadmap_module_updated: bool = False
    placement_readiness_score: float = 0.0
    internship_unlocked: bool = False
