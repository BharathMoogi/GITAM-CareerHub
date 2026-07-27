from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ─── Skill Schemas ────────────────────────────────────────────────────────────

class SkillRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    category: str
    description: Optional[str] = None


class StudentSkillRead(BaseModel):
    """Student skill with proficiency score and source course."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    skill_id: str
    skill_name: str
    skill_category: str
    proficiency_score: float = Field(ge=0.0, le=100.0)
    earned_from_course_id: Optional[str] = None
    earned_from_course_title: Optional[str] = None
    last_updated: datetime


# ─── Course Resource & Outcome Schemas ───────────────────────────────────────

class CourseResourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    resource_type: str
    title: str
    url: str
    provider: Optional[str] = None
    display_order: int
    duration: Optional[str] = None


class CourseOutcomeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: Optional[str] = None
    display_order: int


class CourseSkillRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    skill_id: str
    skill_name: str
    skill_category: str
    proficiency_level: str


# ─── Course Schemas ───────────────────────────────────────────────────────────

class CourseListRead(BaseModel):
    """Lightweight course card for list views."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: Optional[str] = None
    branch_id: str
    branch_name: str
    academic_year_id: str
    year_number: int
    semester_id: str
    semester_number: int
    difficulty: str
    estimated_hours: int
    thumbnail: Optional[str] = None
    status: str
    is_locked: bool = False
    lock_reason: Optional[str] = None
    user_status: str = "NOT_STARTED"
    completion_percentage: float = 0.0
    skills: List[CourseSkillRead] = Field(default_factory=list)


class CourseDetailRead(CourseListRead):
    """Full course detail including resources, outcomes, and skills."""
    learning_objectives: Optional[str] = None
    prerequisites: Optional[str] = None
    resources: List[CourseResourceRead] = Field(default_factory=list)
    outcomes: List[CourseOutcomeRead] = Field(default_factory=list)


# ─── Course Progress Schemas ──────────────────────────────────────────────────

class UpdateCourseProgressRequest(BaseModel):
    """Request body for updating course progress."""
    status: str = Field(..., description="IN_PROGRESS or COMPLETED")
    completion_percentage: Optional[float] = Field(
        None, ge=0.0, le=100.0,
        description="Optional explicit completion percentage (0–100)",
    )


class CourseProgressRead(BaseModel):
    """Response after a course progress update."""
    model_config = ConfigDict(from_attributes=True)

    course_id: str
    course_title: str
    status: str
    completion_percentage: float
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    skills_updated: List[StudentSkillRead] = Field(default_factory=list)
    roadmap_module_updated: bool = False


# ─── Skill Dashboard Schema ───────────────────────────────────────────────────

class SkillDashboardRead(BaseModel):
    """Full student skill dashboard response."""
    total_skills_earned: int
    average_proficiency_score: float
    top_category: Optional[str] = None
    skills: List[StudentSkillRead] = Field(default_factory=list)
