"""
Student Context Aggregator.

This is the heart of the AI Mentor's RAG-from-database approach.
Before EVERY LLM call, the aggregator fetches the student's COMPLETE
profile from all engine tables and builds a rich context dictionary.

Rule: The AI NEVER responds without first loading this context.

Data fetched from:
  - Student Profile (name, branch, year, semester, CGPA)
  - Roadmap Engine (modules, progress, completions)
  - Learning Engine (courses, skills, scores)
  - Project Engine (projects, technologies, status)
  - Certification Engine (certifications, status)
  - Industry Intelligence (company readiness scores)
  - Placement Engine (applications, stages, offers)
  - AI Mentor (goals, conversation history)
"""
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException

logger = logging.getLogger("app.ai.context")


@dataclass
class SkillContext:
    name: str
    score: float
    proficiency_level: str


@dataclass
class ModuleContext:
    title: str
    difficulty: str
    estimated_hours: float
    status: str


@dataclass
class ProjectContext:
    id: str
    title: str
    project_type: str
    difficulty: str
    status: str
    technologies: List[str] = field(default_factory=list)


@dataclass
class CertificationContext:
    id: str
    title: str
    provider: str
    certificate_type: str
    difficulty: str
    estimated_hours: float
    status: str


@dataclass
class ReadinessContext:
    company_name: str
    company_id: str
    overall_score: float
    skill_score: float
    project_score: float
    cert_score: float


@dataclass
class GoalContext:
    id: str
    goal_type: str
    goal_value: str
    target_date: Optional[str]
    status: str


@dataclass
class CourseContext:
    title: str
    platform: str
    difficulty: str
    estimated_hours: float
    status: str
    skills: List[str] = field(default_factory=list)


@dataclass
class StudentContext:
    """
    Complete student context loaded before every AI response.
    All fields are populated from the database — never from the LLM.
    """
    # Identity
    student_id: str
    user_id: str
    student_name: str
    branch: str
    branch_code: str
    current_year: int
    semester: int
    target_role: str

    # Academic progress
    skills: List[SkillContext] = field(default_factory=list)
    completed_courses: int = 0
    total_courses: int = 0
    completed_courses_list: List[CourseContext] = field(default_factory=list)
    recommended_courses: List[CourseContext] = field(default_factory=list)

    # Roadmap
    total_modules: int = 0
    completed_modules: int = 0
    in_progress_modules: int = 0
    pending_modules: List[ModuleContext] = field(default_factory=list)
    recent_completions: List[ModuleContext] = field(default_factory=list)
    completion_rate: float = 0.0

    # Projects
    active_projects: int = 0
    completed_projects: List[ProjectContext] = field(default_factory=list)
    recommended_projects: List[ProjectContext] = field(default_factory=list)

    # Certifications
    certifications_earned: int = 0
    completed_certifications: List[CertificationContext] = field(default_factory=list)
    recommended_certifications: List[CertificationContext] = field(default_factory=list)

    # Industry readiness
    readiness_scores: List[ReadinessContext] = field(default_factory=list)
    avg_readiness_score: float = 0.0
    top_company: Optional[str] = None
    top_company_score: float = 0.0

    # Applications
    internships_applied: int = 0
    placements_applied: int = 0
    shortlisted: int = 0
    selected: int = 0

    # Goals
    goals: List[GoalContext] = field(default_factory=list)

    # Weekly plan
    last_week_completion: float = 0.0
    weekly_goal: str = "Advance your readiness score and complete at least one module"

    # Skill gaps (computed)
    skill_gaps: List[Dict[str, Any]] = field(default_factory=list)
    required_skills: List[Dict[str, Any]] = field(default_factory=list)
    priority_areas: List[Dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        """Convert to a flat dict suitable for Jinja2 template rendering."""
        import dataclasses
        return dataclasses.asdict(self)


class StudentContextAggregator:
    """
    Loads the complete student context from all engine tables.
    Called before every AI tool invocation.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def load(self, user_id: str) -> StudentContext:
        """
        Load full student context for a given user_id.
        Raises NotFoundException if no student profile exists.
        """
        from app.models.user import User
        from app.models.student import Student
        from app.models.branch import Branch
        from app.models.target_role import TargetRole

        # ── 1. Student + Branch + TargetRole ──────────────────────────────
        user_res = await self.db.execute(select(User).where(User.id == user_id))
        user = user_res.scalars().first()
        if not user:
            raise NotFoundException(f"User {user_id} not found")

        stu_res = await self.db.execute(
            select(Student)
            .options(selectinload(Student.branch), selectinload(Student.target_role))
            .where(Student.user_id == user_id)
        )
        student = stu_res.scalars().first()
        if not student:
            raise NotFoundException("Student profile not found. Please complete your profile first.")

        ctx = StudentContext(
            student_id=student.id,
            user_id=user_id,
            student_name=student.full_name,
            branch=student.branch.name if student.branch else "Unknown",
            branch_code=student.branch.code if student.branch else "",
            current_year=student.current_year,
            semester=student.semester,
            target_role=student.target_role.title if student.target_role else "Software Engineer",
        )

        # ── 2. Skills ─────────────────────────────────────────────────────
        await self._load_skills(ctx, student.id)

        # ── 3. Roadmap Progress ───────────────────────────────────────────
        await self._load_roadmap(ctx, student.id)

        # ── 4. Courses ────────────────────────────────────────────────────
        await self._load_courses(ctx, student.id)

        # ── 5. Projects ───────────────────────────────────────────────────
        await self._load_projects(ctx, student.id)

        # ── 6. Certifications ─────────────────────────────────────────────
        await self._load_certifications(ctx, student.id)

        # ── 7. Company Readiness ──────────────────────────────────────────
        await self._load_readiness(ctx, student.id)

        # ── 8. Applications ───────────────────────────────────────────────
        await self._load_applications(ctx, student.id)

        # ── 9. Goals ──────────────────────────────────────────────────────
        await self._load_goals(ctx, student.id)

        # ── 10. Weekly Plan (last week) ────────────────────────────────────
        await self._load_last_plan(ctx, student.id)

        # ── 11. Compute derived fields ────────────────────────────────────
        self._compute_skill_gaps(ctx)
        self._compute_priority_areas(ctx)

        return ctx

    # ── Private loaders ───────────────────────────────────────────────────

    async def _load_skills(self, ctx: StudentContext, student_id: str) -> None:
        from app.models.student_skill import StudentSkill
        from app.models.skill import Skill

        res = await self.db.execute(
            select(StudentSkill, Skill)
            .join(Skill, StudentSkill.skill_id == Skill.id)
            .where(StudentSkill.student_id == student_id)
            .order_by(StudentSkill.proficiency_score.desc())
        )
        for ss, skill in res.all():
            ctx.skills.append(SkillContext(
                name=skill.name,
                score=float(ss.proficiency_score or 0),
                proficiency_level=ss.proficiency_level or "BEGINNER",
            ))

    async def _load_roadmap(self, ctx: StudentContext, student_id: str) -> None:
        from app.models.student_progress import StudentRoadmapProgress
        from app.models.roadmap_module import RoadmapModule
        from sqlalchemy.orm import noload

        res = await self.db.execute(
            select(StudentRoadmapProgress, RoadmapModule)
            .options(noload("*"))
            .join(RoadmapModule, StudentRoadmapProgress.roadmap_module_id == RoadmapModule.id)
            .where(StudentRoadmapProgress.student_id == student_id)
        )
        rows = res.all()
        ctx.total_modules = len(rows)
        for prog, mod in rows:
            if prog.status == "COMPLETED":
                ctx.completed_modules += 1
                ctx.recent_completions.append(ModuleContext(
                    title=mod.title, difficulty=mod.difficulty or "INTERMEDIATE",
                    estimated_hours=float(mod.estimated_hours or 0), status="COMPLETED",
                ))
            elif prog.status == "IN_PROGRESS":
                ctx.in_progress_modules += 1
            else:
                ctx.pending_modules.append(ModuleContext(
                    title=mod.title, difficulty=mod.difficulty or "INTERMEDIATE",
                    estimated_hours=float(mod.estimated_hours or 0), status="NOT_STARTED",
                ))
        ctx.completion_rate = (
            (ctx.completed_modules / ctx.total_modules * 100)
            if ctx.total_modules else 0.0
        )
        ctx.recent_completions = ctx.recent_completions[-5:]
        ctx.pending_modules = ctx.pending_modules[:10]

    async def _load_courses(self, ctx: StudentContext, student_id: str) -> None:
        from app.models.student_course_progress import StudentCourseProgress
        from app.models.course import Course
        from sqlalchemy.orm import noload

        res = await self.db.execute(
            select(StudentCourseProgress, Course)
            .options(noload("*"))
            .join(Course, StudentCourseProgress.course_id == Course.id)
            .where(StudentCourseProgress.student_id == student_id)
        )
        rows = res.all()
        ctx.total_courses = len(rows)
        for prog, course in rows:
            cc = CourseContext(
                title=course.title,
                platform=course.platform or "CareerHub",
                difficulty=course.difficulty or "INTERMEDIATE",
                estimated_hours=float(course.estimated_hours or 0),
                status=prog.status or "NOT_STARTED",
            )
            if prog.status == "COMPLETED":
                ctx.completed_courses += 1
                ctx.completed_courses_list.append(cc)
            else:
                ctx.recommended_courses.append(cc)

    async def _load_projects(self, ctx: StudentContext, student_id: str) -> None:
        from app.models.student_project import StudentProject
        from app.models.project import Project
        from sqlalchemy.orm import noload

        res = await self.db.execute(
            select(StudentProject, Project)
            .options(noload("*"))
            .join(Project, StudentProject.project_id == Project.id)
            .where(StudentProject.student_id == student_id)
        )
        rows = res.all()
        for sp, proj in rows:
            pc = ProjectContext(
                id=proj.id,
                title=proj.title,
                project_type=proj.project_type or "MINI",
                difficulty=proj.difficulty or "INTERMEDIATE",
                status=sp.status or "NOT_STARTED",
            )
            if sp.status in ("COMPLETED", "SUBMITTED"):
                ctx.completed_projects.append(pc)
            elif sp.status == "IN_PROGRESS":
                ctx.active_projects += 1
            else:
                ctx.recommended_projects.append(pc)

        # If no recommended projects, pull un-started projects for branch
        if not ctx.recommended_projects:
            from app.models.project import Project as P
            branch_id = await self._get_branch_id(student_id)
            avail = await self.db.execute(
                select(P)
                .options(noload("*"))
                .where(P.branch_id == branch_id, P.status == "ACTIVE")
                .limit(5)
            )
            for p in avail.scalars().all():
                ctx.recommended_projects.append(ProjectContext(
                    id=p.id, title=p.title, project_type=p.project_type or "MINI",
                    difficulty=p.difficulty or "INTERMEDIATE", status="AVAILABLE",
                ))

    async def _load_certifications(self, ctx: StudentContext, student_id: str) -> None:
        from app.models.student_certification import StudentCertification
        from app.models.certification import Certification
        from sqlalchemy.orm import noload

        res = await self.db.execute(
            select(StudentCertification, Certification)
            .options(noload("*"))
            .join(Certification, StudentCertification.certification_id == Certification.id)
            .where(StudentCertification.student_id == student_id)
        )
        rows = res.all()
        for sc, cert in rows:
            cc = CertificationContext(
                id=cert.id, title=cert.title, provider=cert.provider or "Unknown",
                certificate_type=cert.certificate_type or "COURSE_COMPLETION",
                difficulty=cert.difficulty or "INTERMEDIATE",
                estimated_hours=float(cert.estimated_hours or 0),
                status=sc.status or "NOT_STARTED",
            )
            if sc.status == "COMPLETED":
                ctx.certifications_earned += 1
                ctx.completed_certifications.append(cc)
            else:
                ctx.recommended_certifications.append(cc)

        # Pull branch-relevant certifications if no recommendations
        if not ctx.recommended_certifications:
            from app.models.certification import Certification as C
            branch_id = await self._get_branch_id(student_id)
            avail = await self.db.execute(
                select(C)
                .options(noload("*"))
                .where(C.branch_id == branch_id, C.status == "ACTIVE")
                .limit(5)
            )
            for c in avail.scalars().all():
                ctx.recommended_certifications.append(CertificationContext(
                    id=c.id, title=c.title, provider=c.provider or "Unknown",
                    certificate_type=c.certificate_type or "COURSE_COMPLETION",
                    difficulty=c.difficulty or "INTERMEDIATE",
                    estimated_hours=float(c.estimated_hours or 0),
                    status="AVAILABLE",
                ))

    async def _load_readiness(self, ctx: StudentContext, student_id: str) -> None:
        from app.models.student_company_readiness import StudentCompanyReadiness
        from app.models.company import Company
        from sqlalchemy.orm import noload

        res = await self.db.execute(
            select(StudentCompanyReadiness, Company)
            .options(noload("*"))
            .join(Company, StudentCompanyReadiness.company_id == Company.id)
            .where(
                StudentCompanyReadiness.student_id == student_id,
                StudentCompanyReadiness.job_role_id.is_(None),
            )
            .order_by(StudentCompanyReadiness.overall_score.desc())
            .limit(10)
        )
        scores = []
        for r, c in res.all():
            rc = ReadinessContext(
                company_name=c.name,
                company_id=c.id,
                overall_score=float(r.overall_score or 0),
                skill_score=float(r.skill_score or 0),
                project_score=float(r.project_score or 0),
                cert_score=float(r.cert_score or 0),
            )
            ctx.readiness_scores.append(rc)
            scores.append(rc.overall_score)

        if scores:
            ctx.avg_readiness_score = sum(scores) / len(scores)
            ctx.top_company = ctx.readiness_scores[0].company_name
            ctx.top_company_score = ctx.readiness_scores[0].overall_score

    async def _load_applications(self, ctx: StudentContext, student_id: str) -> None:
        from app.models.placement import StudentApplication

        res = await self.db.execute(
            select(StudentApplication).where(StudentApplication.student_id == student_id)
        )
        apps = res.scalars().all()
        for app in apps:
            if app.internship_id:
                ctx.internships_applied += 1
            else:
                ctx.placements_applied += 1
            if app.status in ("SHORTLISTED", "ONLINE_TEST", "TECHNICAL", "HR"):
                ctx.shortlisted += 1
            elif app.status == "SELECTED":
                ctx.selected += 1

    async def _load_goals(self, ctx: StudentContext, student_id: str) -> None:
        from app.models.ai_mentor import StudentGoal

        res = await self.db.execute(
            select(StudentGoal)
            .where(StudentGoal.student_id == student_id, StudentGoal.status == "ACTIVE")
            .order_by(StudentGoal.created_at.desc())
        )
        for goal in res.scalars().all():
            ctx.goals.append(GoalContext(
                id=goal.id,
                goal_type=goal.goal_type,
                goal_value=goal.goal_value,
                target_date=str(goal.target_date) if goal.target_date else None,
                status=goal.status,
            ))

    async def _load_last_plan(self, ctx: StudentContext, student_id: str) -> None:
        from app.models.ai_mentor import WeeklyPlan

        res = await self.db.execute(
            select(WeeklyPlan)
            .where(WeeklyPlan.student_id == student_id)
            .order_by(WeeklyPlan.week_start.desc())
            .limit(1)
        )
        plan = res.scalars().first()
        if plan:
            ctx.last_week_completion = float(plan.completion_percentage or 0)

    def _compute_skill_gaps(self, ctx: StudentContext) -> None:
        """
        Compare student skills against a baseline set of required skills
        for their target role. Identifies gaps by severity.
        """
        # Role-to-skill mapping for common GITAM target roles
        role_skill_map = {
            "ML Engineer": [("Python", 70), ("TensorFlow", 60), ("Mathematics", 60), ("System Design", 50)],
            "AI Engineer": [("Python", 70), ("Deep Learning", 65), ("MLOps", 55), ("Mathematics", 65)],
            "Data Analyst": [("Python", 60), ("SQL", 70), ("Statistics", 65), ("Power BI", 50)],
            "Embedded Engineer": [("C Programming", 75), ("RTOS", 60), ("Microcontrollers", 70), ("Communication Protocols", 55)],
            "VLSI Engineer": [("Verilog", 70), ("Digital Design", 75), ("Semiconductor Physics", 65)],
            "Software Engineer": [("Python", 65), ("DSA", 70), ("System Design", 60), ("Databases", 55)],
            "Mechanical Design Engineer": [("CAD Software", 70), ("Thermodynamics", 60), ("Material Science", 55)],
            "Power Systems Engineer": [("Power Electronics", 70), ("Circuit Analysis", 65), ("Protection Systems", 60)],
        }
        skill_map = {s.name: s.score for s in ctx.skills}
        target = ctx.target_role

        requirements = role_skill_map.get(target, role_skill_map.get("Software Engineer", []))
        ctx.required_skills = [{"skill_name": sk, "required_level": f"{req}%", "current_level": f"{skill_map.get(sk, 0):.0f}%"} for sk, req in requirements]

        for sk, req in requirements:
            current = skill_map.get(sk, 0)
            if current < req:
                gap = req - current
                severity = "Critical" if gap > 40 else "High" if gap > 20 else "Medium"
                ctx.skill_gaps.append({
                    "skill_name": sk,
                    "required_level": f"{req}%",
                    "current_level": f"{current:.0f}%",
                    "severity": severity,
                    "suggested_resource": f"Search '{sk}' in CareerHub courses",
                })

    def _compute_priority_areas(self, ctx: StudentContext) -> None:
        """Determine top 3 priority areas based on gaps and goals."""
        priorities = []

        # Skills with large gaps = high priority
        for gap in ctx.skill_gaps[:2]:
            priorities.append({
                "name": f"Skill: {gap['skill_name']}",
                "reason": f"Gap severity: {gap['severity']}",
                "suggested_hours": 6,
            })

        # Pending roadmap modules
        if ctx.pending_modules:
            priorities.append({
                "name": f"Roadmap: {ctx.pending_modules[0].title}",
                "reason": "Next required module in your academic roadmap",
                "suggested_hours": 4,
            })

        # Project work if none in progress
        if ctx.active_projects == 0 and ctx.recommended_projects:
            priorities.append({
                "name": f"Start project: {ctx.recommended_projects[0].title}",
                "reason": "Projects are critical for interview credibility",
                "suggested_hours": 5,
            })

        ctx.priority_areas = priorities[:4]

    async def _get_branch_id(self, student_id: str) -> Optional[str]:
        from app.models.student import Student
        res = await self.db.execute(select(Student.branch_id).where(Student.id == student_id))
        row = res.first()
        return row[0] if row else None
