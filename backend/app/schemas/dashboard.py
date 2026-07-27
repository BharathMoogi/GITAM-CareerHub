"""
Pydantic schemas for Dashboard Intelligence Engine.
All analytics are returned as clean, chart-ready JSON structures.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── Generic Chart & Key-Value Schemas ─────────────────────────────────────────

class ChartDataPoint(BaseModel):
    label: str
    value: float
    percentage: Optional[float] = None
    color: Optional[str] = None


class SeriesPoint(BaseModel):
    x: str
    y: float


class ChartSeries(BaseModel):
    name: str
    data: List[SeriesPoint]


class FunnelStage(BaseModel):
    stage: str
    count: int
    conversion_rate: float


# ── Student Dashboard Schemas ──────────────────────────────────────────────────

class StudentProfileSummary(BaseModel):
    student_id: str
    full_name: str
    roll_number: str
    email: str
    branch_name: str
    branch_code: str
    current_year: int
    semester: int
    target_company: Optional[str] = None
    target_role: Optional[str] = None
    avatar_url: Optional[str] = None
    total_xp: Optional[int] = 100
    current_level: Optional[int] = 1
    level_title: Optional[str] = "Explorer"
    badges_earned: Optional[int] = 0



class ProgressMetrics(BaseModel):
    roadmap_completion_pct: float
    course_completion_pct: float
    project_completion_pct: float
    cert_completion_pct: float
    total_applications: int
    active_applications: int
    shortlisted_count: int
    offers_count: int


class ReadinessScores(BaseModel):
    overall_career_readiness: float
    placement_readiness: float
    internship_readiness: float
    interview_readiness: float
    resume_score: float
    portfolio_score: float


class CompanyRankingItem(BaseModel):
    company_id: str
    company_name: str
    overall_score: float
    skill_match: float
    project_match: float
    cert_match: float
    status: str


class LeaderboardRank(BaseModel):
    student_id: str
    student_name: str
    branch_code: str
    roll_number: str
    score: float
    rank: int
    avatar_url: Optional[str] = None


class RecentActivityItem(BaseModel):
    id: str
    title: str
    category: str  # COURSE / PROJECT / CERTIFICATION / APPLICATION / AI_CHAT
    timestamp: str
    details: Optional[str] = None


class StudentDashboardResponse(BaseModel):
    profile: StudentProfileSummary
    progress: ProgressMetrics
    readiness: ReadinessScores
    top_companies: List[CompanyRankingItem]
    upcoming_deadlines: List[Dict[str, Any]]
    todays_tasks: List[Dict[str, Any]]
    weekly_goals: List[Dict[str, Any]]
    learning_hours_total: float
    learning_streak_days: int
    skill_distribution: List[ChartDataPoint]
    branch_rank: int
    branch_total_students: int
    college_rank: int
    college_total_students: int
    recommended_next_action: str
    ai_weekly_summary: str
    recent_activities: List[RecentActivityItem]


# ── Faculty Dashboard Schemas ──────────────────────────────────────────────────

class StudentRiskItem(BaseModel):
    student_id: str
    student_name: str
    roll_number: str
    branch_code: str
    semester: int
    readiness_score: float
    completion_rate: float
    risk_level: str  # HIGH / MEDIUM / LOW
    reason: str


class FacultyDashboardResponse(BaseModel):
    department_code: str
    department_name: str
    total_students: int
    average_readiness_score: float
    placement_eligible_count: int
    internship_eligible_count: int
    student_progress_distribution: List[ChartDataPoint]
    skill_heatmap: List[ChartDataPoint]
    placement_readiness_chart: List[ChartDataPoint]
    internship_readiness_chart: List[ChartDataPoint]
    students_at_risk: List[StudentRiskItem]
    leaderboard_top_10: List[LeaderboardRank]
    certification_stats: Dict[str, Any]
    project_stats: Dict[str, Any]
    ai_usage_stats: Dict[str, Any]


# ── Placement Officer Dashboard Schemas ────────────────────────────────────────

class CompanyEligibilitySummary(BaseModel):
    company_id: str
    company_name: str
    industry: str
    total_eligible_students: int
    openings_count: int
    min_readiness_required: float


class PlacementDashboardResponse(BaseModel):
    total_eligible_students: int
    total_placed_students: int
    placement_rate_pct: float
    company_eligibility: List[CompanyEligibilitySummary]
    application_funnel: List[FunnelStage]
    interview_funnel: List[FunnelStage]
    offer_funnel: List[FunnelStage]
    branch_wise_placements: List[ChartDataPoint]
    hiring_companies_count: int
    active_drives_count: int
    upcoming_drives: List[Dict[str, Any]]


# ── Admin Dashboard Schemas ────────────────────────────────────────────────────

class AdminDashboardResponse(BaseModel):
    daily_active_users: int
    weekly_active_users: int
    monthly_active_users: int
    platform_usage: Dict[str, Any]
    api_usage: Dict[str, Any]
    database_statistics: Dict[str, Any]
    storage_statistics: Dict[str, Any]
    companies_count: int
    courses_count: int
    projects_count: int
    certifications_count: int
    system_notifications: List[Dict[str, Any]]
    ai_usage_summary: Dict[str, Any]
    system_health: Dict[str, Any]


# ── Generic Leaderboard Response ───────────────────────────────────────────────

class LeaderboardResponse(BaseModel):
    branch_code: Optional[str] = None
    total_entries: int
    leaderboard: List[LeaderboardRank]
