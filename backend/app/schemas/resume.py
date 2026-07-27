"""
Pydantic schemas for Resume Intelligence Engine API.
"""
from datetime import date
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── Requests ──────────────────────────────────────────────────────────────────

class ResumeHeaderUpdate(BaseModel):
    headline: str = Field(..., min_length=2, max_length=255)
    summary: str = Field(..., min_length=10, max_length=2000)


class AddExperienceRequest(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=255)
    role_title: str = Field(..., min_length=1, max_length=255)
    start_date: date
    end_date: Optional[date] = None
    is_current: bool = False
    location: Optional[str] = None
    bullet_points: List[str] = Field(default_factory=list)


class AddHackathonRequest(BaseModel):
    event_name: str = Field(..., min_length=1, max_length=255)
    project_title: str = Field(..., min_length=1, max_length=255)
    prize_rank: Optional[str] = None
    date_held: Optional[date] = None
    repo_url: Optional[str] = None


class AddPublicationRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    journal_publisher: Optional[str] = None
    publication_date: Optional[date] = None
    paper_url: Optional[str] = None
    authors: Optional[str] = None


class AddPatentRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    patent_number: Optional[str] = None
    filing_date: Optional[date] = None
    status: str = Field(default="FILED")
    url: Optional[str] = None


class ResumeReviewRequest(BaseModel):
    job_description: Optional[str] = Field(None, max_length=4000)


# ── Responses ─────────────────────────────────────────────────────────────────

class ResumeProfileResponse(BaseModel):
    id: str
    student_id: str
    headline: Optional[str] = None
    summary: Optional[str] = None
    target_role: str
    experiences: List[Dict[str, Any]]
    hackathons: List[Dict[str, Any]]
    publications: List[Dict[str, Any]]
    patents: List[Dict[str, Any]]
    achievements: List[Dict[str, Any]]
    volunteering: List[Dict[str, Any]]


class GenerateATSResponse(BaseModel):
    ats_resume_json: Dict[str, Any]
    pdf_metadata: Dict[str, Any]
    scores: Dict[str, float]
    skill_gap_analysis: Dict[str, Any]
    recommended_improvements: List[str]
    integrations_status: Dict[str, bool]


class BulletImprovementItem(BaseModel):
    original: str
    improved_star: str
    action_verb: str


class ResumeReviewResponse(BaseModel):
    overall_feedback: str
    bullet_improvements: List[BulletImprovementItem]
    generated_project_bullets: List[str]
    skill_recommendations: List[str]


class ResumeScoreResponse(BaseModel):
    scores: Dict[str, float]
    skill_gap_analysis: Dict[str, Any]
    recommended_improvements: List[str]


class PortfolioJSONResponse(BaseModel):
    student_id: str
    full_name: str
    headline: str
    bio: str
    social_links: Dict[str, str]
    featured_projects: List[Dict[str, Any]]
    skills: List[str]
    certifications: List[Dict[str, Any]]
    portfolio_url_slug: str
    theme: str


class PortfolioReviewResponse(BaseModel):
    portfolio_score: float
    strengths: List[str]
    suggestions: List[str]
    ai_review_narrative: str
