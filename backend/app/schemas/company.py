"""
Pydantic schemas for the Industry Intelligence Engine.

Covers:
- Company (list + detail)
- JobRole
- ReadinessScore
- StudentCompanyReadiness
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ─── Sub-schemas ─────────────────────────────────────────────────────────────

class CompanySkillRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    skill_id: str
    skill_name: str
    skill_category: str
    required_level: str
    weightage: float


class CompanyCourseLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    course_id: str
    course_title: str
    difficulty: str
    estimated_hours: Optional[int] = None
    importance: str


class CompanyProjectLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    project_id: str
    project_title: str
    difficulty: str
    project_type: str
    importance: str


class CompanyCertificationLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    certification_id: str
    certification_title: str
    provider: str
    difficulty: str
    importance: str


class InterviewRoundRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    round_name: str
    round_order: int
    description: Optional[str] = None


class InterviewQuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    question: str
    difficulty: str
    expected_answer: Optional[str] = None
    category: str
    job_role_title: Optional[str] = None


class JobRoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    role_category: str
    employment_type: str
    experience_level: str
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    location: Optional[str] = None
    job_description: Optional[str] = None
    status: str


# ─── Company List schema ──────────────────────────────────────────────────────

class CompanyListRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    logo: Optional[str] = None
    website: Optional[str] = None
    industry: str
    headquarters: Optional[str] = None
    description: Optional[str] = None
    company_size: Optional[str] = None
    careers_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    glassdoor_url: Optional[str] = None
    is_hiring: bool

    # Student context
    readiness_score: float = Field(0.0, description="Student's overall readiness score 0-100")
    readiness_label: str = Field("NOT_ASSESSED", description="WEAK / MODERATE / STRONG / READY")
    applied_skills_count: int = Field(0, description="Number of required skills student already has")
    total_skills_count: int = Field(0, description="Total required skills for this company")

    job_roles: List[JobRoleRead] = Field(default_factory=list)
    top_skills: List[CompanySkillRead] = Field(default_factory=list)


# ─── Company Detail schema ────────────────────────────────────────────────────

class CompanyDetailRead(CompanyListRead):
    recommended_courses: List[CompanyCourseLinkRead] = Field(default_factory=list)
    recommended_projects: List[CompanyProjectLinkRead] = Field(default_factory=list)
    recommended_certifications: List[CompanyCertificationLinkRead] = Field(default_factory=list)
    interview_rounds: List[InterviewRoundRead] = Field(default_factory=list)
    interview_questions: List[InterviewQuestionRead] = Field(default_factory=list)

    # Detailed readiness breakdown
    course_score: float = 0.0
    project_score: float = 0.0
    skill_score: float = 0.0
    certification_score: float = 0.0
    gap_skills: List[str] = Field(default_factory=list, description="Skills the student still needs to acquire")


# ─── Readiness Score schemas ──────────────────────────────────────────────────

class ReadinessScoreRead(BaseModel):
    """Lightweight readiness card for a student-company pair."""
    company_id: str
    company_name: str
    company_logo: Optional[str] = None
    industry: str
    overall_score: float
    course_score: float
    project_score: float
    skill_score: float
    certification_score: float
    readiness_label: str
    gap_skills: List[str] = Field(default_factory=list)
    last_updated: datetime


class StudentReadinessSummaryRead(BaseModel):
    """Full readiness snapshot for a student across all companies."""
    student_id: str
    student_name: str
    branch_name: str
    current_semester: int
    average_readiness: float
    top_company: Optional[str] = None
    top_company_score: float = 0.0
    companies: List[ReadinessScoreRead] = Field(default_factory=list)
