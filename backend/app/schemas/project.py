from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


# ─── Sub-schemas ──────────────────────────────────────────────────────────────

class ProjectTechnologyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    category: str
    description: Optional[str] = None


class ProjectSkillRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    skill_id: str
    skill_name: str
    skill_category: str
    required_level: str


class ProjectResourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    resource_type: str
    title: str
    url: str
    display_order: int


class ProjectDeliverableRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    description: Optional[str] = None
    display_order: int


class ProjectInterviewQuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    question: str
    difficulty: str
    expected_answer: Optional[str] = None


class ProjectResumePointRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    resume_point: str
    display_order: int


# ─── Project List (card view) ─────────────────────────────────────────────────

class ProjectListRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    slug: str
    description: Optional[str] = None
    project_type: str
    difficulty: str
    estimated_duration: Optional[str] = None
    branch_id: str
    branch_name: str
    year_number: int
    semester_number: int
    status: str
    thumbnail: Optional[str] = None

    # Student context
    is_locked: bool = False
    lock_reason: Optional[str] = None
    user_status: str = "NOT_STARTED"
    review_score: Optional[float] = None

    skills: List[ProjectSkillRead] = Field(default_factory=list)
    technologies: List[ProjectTechnologyRead] = Field(default_factory=list)


# ─── Project Detail (full view) ───────────────────────────────────────────────

class ProjectDetailRead(ProjectListRead):
    problem_statement: Optional[str] = None
    real_world_impact: Optional[str] = None
    resources: List[ProjectResourceRead] = Field(default_factory=list)
    deliverables: List[ProjectDeliverableRead] = Field(default_factory=list)
    interview_questions: List[ProjectInterviewQuestionRead] = Field(default_factory=list)
    resume_points: List[ProjectResumePointRead] = Field(default_factory=list)

    github_repository: Optional[str] = None
    demo_url: Optional[str] = None
    report_url: Optional[str] = None
    submission_date: Optional[datetime] = None


# ─── Student Project schemas ──────────────────────────────────────────────────

class StudentProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    project_title: str
    project_type: str
    difficulty: str
    branch_name: str
    year_number: int
    semester_number: int
    status: str
    github_repository: Optional[str] = None
    demo_url: Optional[str] = None
    report_url: Optional[str] = None
    submission_date: Optional[datetime] = None
    review_score: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# ─── Progress Update schemas ──────────────────────────────────────────────────

class UpdateProjectProgressRequest(BaseModel):
    status: str = Field(..., description="IN_PROGRESS or COMPLETED")


class SubmitProjectRequest(BaseModel):
    github_repository: str = Field(..., min_length=5, description="GitHub repository URL")
    demo_url: Optional[str] = Field(None, description="Live demo or video URL")
    report_url: Optional[str] = Field(None, description="Project report URL (PDF or Drive link)")


class ProjectProgressRead(BaseModel):
    project_id: str
    project_title: str
    status: str
    github_repository: Optional[str] = None
    demo_url: Optional[str] = None
    report_url: Optional[str] = None
    submission_date: Optional[datetime] = None
    review_score: Optional[float] = None
    skills_updated: List[dict] = Field(default_factory=list)
    roadmap_module_updated: bool = False
