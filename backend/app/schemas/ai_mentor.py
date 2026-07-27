"""
Pydantic schemas for the AI Mentor Engine API.
"""
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


# ── Request schemas ───────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000, description="User's message to the AI Mentor")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID, or null to start new")
    tool: str = Field(
        default="career_advisor",
        description=(
            "AI tool to use. One of: career_advisor, roadmap_advisor, project_recommender, "
            "certification_recommender, company_readiness, skill_gap_analyzer, "
            "resume_advisor, interview_coach, learning_planner, weekly_planner"
        ),
    )
    stream: bool = Field(default=False, description="If true, response is streamed via SSE")

    @field_validator("tool")
    @classmethod
    def validate_tool(cls, v: str) -> str:
        valid = {
            "career_advisor", "roadmap_advisor", "project_recommender",
            "certification_recommender", "company_readiness", "skill_gap_analyzer",
            "resume_advisor", "interview_coach", "learning_planner", "weekly_planner",
        }
        if v not in valid:
            raise ValueError(f"Invalid tool. Must be one of: {', '.join(sorted(valid))}")
        return v


class GoalCreateRequest(BaseModel):
    goal_type: str = Field(
        ...,
        description="One of: TARGET_COMPANY, TARGET_ROLE, HIGHER_STUDIES, RESEARCH, ENTREPRENEURSHIP",
    )
    goal_value: str = Field(..., min_length=1, max_length=500, description="e.g. 'Google India' or 'ML Engineer'")
    target_date: Optional[date] = Field(None, description="Target date to achieve the goal")

    @field_validator("goal_type")
    @classmethod
    def validate_goal_type(cls, v: str) -> str:
        valid = {"TARGET_COMPANY", "TARGET_ROLE", "HIGHER_STUDIES", "RESEARCH", "ENTREPRENEURSHIP"}
        if v not in valid:
            raise ValueError(f"Invalid goal_type. Must be one of: {', '.join(valid)}")
        return v


class GoalStatusUpdate(BaseModel):
    status: str = Field(..., description="One of: ACTIVE, ACHIEVED, DROPPED")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid = {"ACTIVE", "ACHIEVED", "DROPPED"}
        if v not in valid:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid)}")
        return v


# ── Response schemas ──────────────────────────────────────────────────────────

class ChatResponse(BaseModel):
    conversation_id: str
    response: str
    student_name: str
    context_loaded: bool = True
    cached: bool = False
    provider: str


class ConversationSummary(BaseModel):
    id: str
    title: str
    updated_at: str


class MessageRead(BaseModel):
    id: str
    role: str
    message: str
    created_at: str


class GoalRead(BaseModel):
    id: str
    goal_type: str
    goal_value: str
    target_date: Optional[str]
    status: str
    created_at: Optional[str] = None


class GoalCreateResponse(BaseModel):
    id: str
    goal_type: str
    goal_value: str
    target_date: Optional[str]
    status: str
    message: str


class WeeklyPlanTask(BaseModel):
    day: str
    task: str
    hours: float


class WeeklyPlanResponse(BaseModel):
    id: Optional[str] = None
    week_start: str
    tasks: List[Dict[str, Any]]
    estimated_hours: float
    completion_percentage: float
    ai_narrative: Optional[str] = None
    cached: bool = False


class ReadinessEntry(BaseModel):
    company: str
    overall: float
    skill: float
    project: float
    cert: float
    status: str


class CompanyReadinessResponse(BaseModel):
    readiness_scores: List[ReadinessEntry]
    avg_readiness: float
    top_company: Optional[str]
    ai_analysis: str


class ProjectSuggestionResponse(BaseModel):
    recommended_projects: List[Dict[str, Any]]
    ai_analysis: str
    student_skills: List[Dict[str, Any]]


class CourseSuggestionResponse(BaseModel):
    recommended_courses: List[Dict[str, Any]]
    ai_analysis: str
    skill_gaps: List[Dict[str, Any]]


class CertificationSuggestionResponse(BaseModel):
    recommended_certifications: List[Dict[str, Any]]
    completed_certifications: List[Dict[str, Any]]
    ai_analysis: str


class InterviewPrepResponse(BaseModel):
    target_role: str
    goals: List[Dict[str, Any]]
    projects_for_resume: List[Dict[str, Any]]
    certifications: List[Dict[str, Any]]
    ai_prep_plan: str


class ProviderInfoResponse(BaseModel):
    provider: str
    model: str
    available: bool
    available_providers: List[str]
    templates: List[str]
    rag_status: str
