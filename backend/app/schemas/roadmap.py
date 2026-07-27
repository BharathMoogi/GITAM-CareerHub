from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ─── Module Types ────────────────────────────────────────────────────────────

class ModuleType:
    COURSE = "COURSE"
    QUIZ = "QUIZ"
    PROJECT = "PROJECT"
    CERTIFICATION = "CERTIFICATION"
    SKILL = "SKILL"
    INTERNSHIP = "INTERNSHIP"
    PLACEMENT = "PLACEMENT"
    AI_LEARNING = "AI_LEARNING"
    PROFILE_SETUP = "PROFILE_SETUP"


class ProgressStatus:
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"


# ─── Master Lookup Schemas ────────────────────────────────────────────────────

class AcademicYearRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    year_number: int
    name: str


class SemesterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    semester_number: int
    name: str
    academic_year_id: str


# ─── Roadmap Module Schemas ───────────────────────────────────────────────────

class DependencyPrerequisiteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    prerequisite_module_id: str
    prerequisite_module_name: str


class RoadmapModuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    roadmap_id: str
    module_name: str
    module_type: str
    display_order: int
    is_required: bool
    estimated_hours: int

    # Progress state for current student
    user_status: str = ProgressStatus.NOT_STARTED
    completion_percentage: float = 0.0
    is_locked: bool = False
    lock_reason: Optional[str] = None
    prerequisites: List[str] = Field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# ─── Roadmap Schemas ──────────────────────────────────────────────────────────

class RoadmapRead(BaseModel):
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
    display_order: int
    is_active: bool
    modules: List[RoadmapModuleRead] = Field(default_factory=list)
    total_estimated_hours: int = 0


# ─── Progress Schemas ─────────────────────────────────────────────────────────

class StudentProgressRead(BaseModel):
    """Comprehensive student progress view across all modules."""
    overall_completion_percentage: float
    completed_modules_count: int
    in_progress_modules_count: int
    total_modules_count: int
    total_estimated_hours: int
    completed_estimated_hours: int
    completed_modules: List[RoadmapModuleRead] = Field(default_factory=list)
    in_progress_modules: List[RoadmapModuleRead] = Field(default_factory=list)
    locked_modules: List[RoadmapModuleRead] = Field(default_factory=list)
    upcoming_modules: List[RoadmapModuleRead] = Field(default_factory=list)


class UpdateModuleProgressRequest(BaseModel):
    """Payload to update a student's module progress status."""
    status: str = Field(
        ...,
        description="New module status: IN_PROGRESS, COMPLETED, or SKIPPED (admin only)",
    )
    completion_percentage: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Optional completion percentage override (0.0-100.0)",
    )

    def validate_status(self) -> "UpdateModuleProgressRequest":
        allowed = [
            ProgressStatus.IN_PROGRESS,
            ProgressStatus.COMPLETED,
            ProgressStatus.SKIPPED,
        ]
        if self.status not in allowed:
            raise ValueError(f"status must be one of: {', '.join(allowed)}")
        return self
