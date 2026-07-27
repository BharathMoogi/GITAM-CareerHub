import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.course import Course
from app.models.project import Project
from app.models.project_technology import ProjectTechnology
from app.models.roadmap import Roadmap
from app.models.roadmap_module import RoadmapModule
from app.models.roadmap_dependency import RoadmapModuleDependency
from app.models.student import Student
from app.models.student_course_progress import StudentCourseProgress
from app.models.student_project import StudentProject
from app.models.student_progress import StudentRoadmapProgress
from app.models.student_skill import StudentSkill
from app.schemas.project import (
    ProjectDetailRead,
    ProjectDeliverableRead,
    ProjectInterviewQuestionRead,
    ProjectListRead,
    ProjectProgressRead,
    ProjectResourceRead,
    ProjectResumePointRead,
    ProjectSkillRead,
    ProjectTechnologyRead,
    StudentProjectRead,
    SubmitProjectRequest,
    UpdateProjectProgressRequest,
)
from app.schemas.roadmap import ProgressStatus

logger = logging.getLogger("app.services.project_service")

ALLOWED_PROJECT_PROGRESS_STATUSES = ["IN_PROGRESS", "COMPLETED"]


class ProjectService:
    """
    Business logic for the Project Intelligence Engine.
    Handles project listings, lock resolution, submission, progress updates,
    skill calculation, and roadmap cascade.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_student(self, user_id: str) -> Student:
        res = await self.db.execute(select(Student).where(Student.user_id == user_id))
        student = res.unique().scalars().first()
        if not student:
            raise NotFoundException(message="Student profile not found.")
        return student

    async def _get_student_project_map(self, student_id: str) -> Dict[str, StudentProject]:
        res = await self.db.execute(
            select(StudentProject).where(StudentProject.student_id == student_id)
        )
        rows = res.unique().scalars().all()
        return {r.project_id: r for r in rows}

    async def _resolve_project_lock(
        self,
        project: Project,
        student: Student,
    ) -> Tuple[bool, Optional[str]]:
        """
        Projects unlock ONLY when:
        1. Current student semester >= project semester (not a future semester).
        2. Required courses in the same semester/branch are COMPLETED.
        3. Required skills are achieved at minimum required proficiency.
        4. Linked RoadmapModule prerequisite dependencies are COMPLETED.
        """
        # Rule 1 — Semester boundary
        if project.semester.semester_number > student.semester:
            return True, (
                f"Future semester locked "
                f"(Semester {project.semester.semester_number} requires completion of Semester {student.semester})"
            )

        # Rule 2 — Required courses completed
        course_res = await self.db.execute(
            select(Course).where(
                Course.branch_id == project.branch_id,
                Course.semester_id == project.semester_id,
                Course.status == "PUBLISHED",
            )
        )
        required_courses = course_res.unique().scalars().all()
        for course in required_courses:
            prog_res = await self.db.execute(
                select(StudentCourseProgress).where(
                    StudentCourseProgress.student_id == student.id,
                    StudentCourseProgress.course_id == course.id,
                )
            )
            prog = prog_res.unique().scalars().first()
            if not prog or prog.status != "COMPLETED":
                return True, f"Required course not completed: '{course.title}'"

        # Rule 3 — Required skills achieved
        level_score_map = {"BEGINNER": 20.0, "INTERMEDIATE": 45.0, "ADVANCED": 75.0}
        for ps in project.project_skills:
            req_score = level_score_map.get(ps.required_level, 20.0)
            ss_res = await self.db.execute(
                select(StudentSkill).where(
                    StudentSkill.student_id == student.id,
                    StudentSkill.skill_id == ps.skill_id,
                )
            )
            ss = ss_res.unique().scalars().first()
            if not ss or ss.proficiency_score < req_score:
                return True, f"Required skill '{ps.skill.name}' ({ps.required_level}) not yet achieved"

        # Rule 4 — Roadmap Module unlock check
        if project.roadmap_module_id:
            module = await self.db.get(RoadmapModule, project.roadmap_module_id)
            if module:
                dep_res = await self.db.execute(
                    select(RoadmapModuleDependency).where(
                        RoadmapModuleDependency.module_id == module.id
                    )
                )
                deps = dep_res.unique().scalars().all()
                for dep in deps:
                    prog_res = await self.db.execute(
                        select(StudentRoadmapProgress).where(
                            StudentRoadmapProgress.student_id == student.id,
                            StudentRoadmapProgress.roadmap_module_id == dep.depends_on_module_id,
                        )
                    )
                    prog = prog_res.unique().scalars().first()
                    if not prog or prog.status not in (ProgressStatus.COMPLETED, ProgressStatus.SKIPPED):
                        prereq_module = await self.db.get(RoadmapModule, dep.depends_on_module_id)
                        prereq_name = prereq_module.module_name if prereq_module else dep.depends_on_module_id
                        return True, f"Prerequisite roadmap module not completed: '{prereq_name}'"

        return False, None

    def _build_project_list_item(
        self,
        project: Project,
        student_project: Optional[StudentProject],
        is_locked: bool,
        lock_reason: Optional[str],
    ) -> ProjectListRead:
        return ProjectListRead(
            id=project.id,
            title=project.title,
            slug=project.slug,
            description=project.description,
            project_type=project.project_type,
            difficulty=project.difficulty,
            estimated_duration=project.estimated_duration,
            branch_id=project.branch_id,
            branch_name=project.branch.name,
            year_number=project.academic_year.year_number,
            semester_number=project.semester.semester_number,
            status=project.status,
            thumbnail=project.thumbnail,
            is_locked=is_locked,
            lock_reason=lock_reason,
            user_status=student_project.status if student_project else "NOT_STARTED",
            review_score=student_project.review_score if student_project else None,
            skills=[
                ProjectSkillRead(
                    skill_id=ps.skill_id,
                    skill_name=ps.skill.name,
                    skill_category=ps.skill.category,
                    required_level=ps.required_level,
                )
                for ps in project.project_skills
            ],
            technologies=[
                ProjectTechnologyRead(
                    id=ptm.technology.id,
                    name=ptm.technology.name,
                    category=ptm.technology.category,
                    description=ptm.technology.description,
                )
                for ptm in project.technology_maps
            ],
        )

    def _build_project_detail(
        self,
        project: Project,
        student_project: Optional[StudentProject],
        is_locked: bool,
        lock_reason: Optional[str],
    ) -> ProjectDetailRead:
        base = self._build_project_list_item(project, student_project, is_locked, lock_reason)
        return ProjectDetailRead(
            **base.model_dump(),
            problem_statement=project.problem_statement,
            real_world_impact=project.real_world_impact,
            resources=[
                ProjectResourceRead(
                    id=r.id, resource_type=r.resource_type, title=r.title, url=r.url, display_order=r.display_order
                )
                for r in sorted(project.resources, key=lambda x: x.display_order)
            ],
            deliverables=[
                ProjectDeliverableRead(
                    id=d.id, title=d.title, description=d.description, display_order=d.display_order
                )
                for d in sorted(project.deliverables, key=lambda x: x.display_order)
            ],
            interview_questions=[
                ProjectInterviewQuestionRead(
                    id=q.id, question=q.question, difficulty=q.difficulty, expected_answer=q.expected_answer
                )
                for q in project.interview_questions
            ],
            resume_points=[
                ProjectResumePointRead(
                    id=rp.id, resume_point=rp.resume_point, display_order=rp.display_order
                )
                for rp in sorted(project.resume_points, key=lambda x: x.display_order)
            ],
            github_repository=student_project.github_repository if student_project else None,
            demo_url=student_project.demo_url if student_project else None,
            report_url=student_project.report_url if student_project else None,
            submission_date=student_project.submission_date if student_project else None,
        )

    # ─── Public API Methods ────────────────────────────────────────────────────

    async def list_projects(
        self,
        user_id: str,
        branch: Optional[str] = None,
        year: Optional[int] = None,
        semester: Optional[int] = None,
        difficulty: Optional[str] = None,
        technology: Optional[str] = None,
        skill: Optional[str] = None,
        project_type: Optional[str] = None,
    ) -> List[ProjectListRead]:
        student = await self._get_student(user_id)

        query = select(Project).where(Project.status == "PUBLISHED")
        query = query.where(Project.branch_id == student.branch_id)

        res = await self.db.execute(query)
        projects: List[Project] = res.unique().scalars().all()

        # Apply post-load filters
        if year:
            projects = [p for p in projects if p.academic_year.year_number == year]
        if semester:
            projects = [p for p in projects if p.semester.semester_number == semester]
        if difficulty:
            projects = [p for p in projects if p.difficulty.upper() == difficulty.upper()]
        if project_type:
            projects = [p for p in projects if p.project_type.upper() == project_type.upper()]
        if technology:
            tech_lower = technology.lower()
            projects = [
                p for p in projects
                if any(ptm.technology.name.lower() == tech_lower for ptm in p.technology_maps)
            ]
        if skill:
            skill_lower = skill.lower()
            projects = [
                p for p in projects
                if any(ps.skill.name.lower() == skill_lower for ps in p.project_skills)
            ]

        difficulty_order = {"BEGINNER": 1, "INTERMEDIATE": 2, "ADVANCED": 3}
        projects.sort(key=lambda p: (
            p.academic_year.year_number,
            p.semester.semester_number,
            difficulty_order.get(p.difficulty, 99),
        ))

        sp_map = await self._get_student_project_map(student.id)

        output = []
        for project in projects:
            is_locked, lock_reason = await self._resolve_project_lock(project, student)
            sp = sp_map.get(project.id)
            output.append(self._build_project_list_item(project, sp, is_locked, lock_reason))

        return output

    async def get_project_detail(self, user_id: str, project_id: str) -> ProjectDetailRead:
        student = await self._get_student(user_id)

        res = await self.db.execute(select(Project).where(Project.id == project_id))
        project = res.unique().scalars().first()
        if not project:
            raise NotFoundException(message=f"Project '{project_id}' not found.")

        sp_map = await self._get_student_project_map(student.id)
        sp = sp_map.get(project.id)
        is_locked, lock_reason = await self._resolve_project_lock(project, student)

        return self._build_project_detail(project, sp, is_locked, lock_reason)

    async def update_project_progress(
        self,
        user_id: str,
        project_id: str,
        payload: UpdateProjectProgressRequest,
    ) -> ProjectProgressRead:
        if payload.status not in ALLOWED_PROJECT_PROGRESS_STATUSES:
            raise BadRequestException(
                message=f"Invalid status '{payload.status}'. Allowed: {', '.join(ALLOWED_PROJECT_PROGRESS_STATUSES)}"
            )

        student = await self._get_student(user_id)

        res = await self.db.execute(select(Project).where(Project.id == project_id))
        project = res.unique().scalars().first()
        if not project:
            raise NotFoundException(message=f"Project '{project_id}' not found.")

        is_locked, lock_reason = await self._resolve_project_lock(project, student)
        if is_locked:
            raise BadRequestException(message=f"Cannot update progress — project is locked: {lock_reason}")

        sp_map = await self._get_student_project_map(student.id)
        sp = sp_map.get(project_id)
        now = datetime.now(timezone.utc)

        if not sp:
            sp = StudentProject(
                student_id=student.id,
                project_id=project_id,
                status=payload.status,
            )
            self.db.add(sp)

        sp.status = payload.status
        if payload.status == "IN_PROGRESS" and not sp.started_at:
            sp.started_at = now
        elif payload.status == "COMPLETED":
            sp.completed_at = now
            if not sp.started_at:
                sp.started_at = now

        skills_updated = []
        roadmap_updated = False

        if payload.status == "COMPLETED":
            skills_updated, roadmap_updated = await self._process_completion_rewards(student, project, now)

        await self.db.commit()
        await self.db.refresh(sp)

        return ProjectProgressRead(
            project_id=project_id,
            project_title=project.title,
            status=sp.status,
            github_repository=sp.github_repository,
            demo_url=sp.demo_url,
            report_url=sp.report_url,
            submission_date=sp.submission_date,
            review_score=sp.review_score,
            skills_updated=skills_updated,
            roadmap_module_updated=roadmap_updated,
        )

    async def submit_project(
        self,
        user_id: str,
        project_id: str,
        payload: SubmitProjectRequest,
    ) -> ProjectProgressRead:
        student = await self._get_student(user_id)

        res = await self.db.execute(select(Project).where(Project.id == project_id))
        project = res.unique().scalars().first()
        if not project:
            raise NotFoundException(message=f"Project '{project_id}' not found.")

        is_locked, lock_reason = await self._resolve_project_lock(project, student)
        if is_locked:
            raise BadRequestException(message=f"Cannot submit — project is locked: {lock_reason}")

        sp_map = await self._get_student_project_map(student.id)
        sp = sp_map.get(project_id)
        now = datetime.now(timezone.utc)

        if not sp:
            sp = StudentProject(
                student_id=student.id,
                project_id=project_id,
                status="SUBMITTED",
            )
            self.db.add(sp)

        sp.status = "SUBMITTED"
        sp.github_repository = payload.github_repository
        sp.demo_url = payload.demo_url
        sp.report_url = payload.report_url
        sp.submission_date = now
        if not sp.started_at:
            sp.started_at = now

        # Submitting automatically moves to COMPLETED for instant portfolio feedback & skill boost
        sp.status = "COMPLETED"
        sp.completed_at = now

        skills_updated, roadmap_updated = await self._process_completion_rewards(student, project, now)

        await self.db.commit()
        await self.db.refresh(sp)

        return ProjectProgressRead(
            project_id=project_id,
            project_title=project.title,
            status=sp.status,
            github_repository=sp.github_repository,
            demo_url=sp.demo_url,
            report_url=sp.report_url,
            submission_date=sp.submission_date,
            review_score=sp.review_score,
            skills_updated=skills_updated,
            roadmap_module_updated=roadmap_updated,
        )

    async def get_my_projects(self, user_id: str) -> List[StudentProjectRead]:
        student = await self._get_student(user_id)

        res = await self.db.execute(
            select(StudentProject).where(StudentProject.student_id == student.id)
        )
        sps = res.unique().scalars().all()

        output = []
        for sp in sps:
            p = sp.project
            output.append(
                StudentProjectRead(
                    id=sp.id,
                    project_id=p.id,
                    project_title=p.title,
                    project_type=p.project_type,
                    difficulty=p.difficulty,
                    branch_name=p.branch.name,
                    year_number=p.academic_year.year_number,
                    semester_number=p.semester.semester_number,
                    status=sp.status,
                    github_repository=sp.github_repository,
                    demo_url=sp.demo_url,
                    report_url=sp.report_url,
                    submission_date=sp.submission_date,
                    review_score=sp.review_score,
                    started_at=sp.started_at,
                    completed_at=sp.completed_at,
                )
            )

        output.sort(key=lambda x: x.started_at or datetime.min, reverse=True)
        return output

    async def _process_completion_rewards(
        self, student: Student, project: Project, now: datetime
    ) -> Tuple[List[dict], bool]:
        skills_updated = []
        roadmap_updated = False

        # 1. Increase Student Skills
        boost_map = {"MINI": 15.0, "MINOR": 25.0, "MAJOR": 35.0, "CAPSTONE": 50.0}
        score_boost = boost_map.get(project.project_type, 20.0)

        for ps in project.project_skills:
            ss_res = await self.db.execute(
                select(StudentSkill).where(
                    StudentSkill.student_id == student.id,
                    StudentSkill.skill_id == ps.skill_id,
                )
            )
            ss = ss_res.unique().scalars().first()
            if ss:
                ss.proficiency_score = min(100.0, ss.proficiency_score + score_boost)
                ss.last_updated = now
            else:
                ss = StudentSkill(
                    student_id=student.id,
                    skill_id=ps.skill_id,
                    proficiency_score=score_boost,
                    earned_from_course_id=None,
                    last_updated=now,
                )
                self.db.add(ss)
                await self.db.flush()

            skills_updated.append(
                {
                    "skill_id": ps.skill_id,
                    "skill_name": ps.skill.name,
                    "new_score": ss.proficiency_score,
                }
            )

        # 2. Update Roadmap Progress & unlock dependent Certification
        if project.roadmap_module_id:
            rmp_res = await self.db.execute(
                select(StudentRoadmapProgress).where(
                    StudentRoadmapProgress.student_id == student.id,
                    StudentRoadmapProgress.roadmap_module_id == project.roadmap_module_id,
                )
            )
            rmp = rmp_res.unique().scalars().first()
            if not rmp:
                rmp = StudentRoadmapProgress(
                    student_id=student.id,
                    roadmap_module_id=project.roadmap_module_id,
                    status=ProgressStatus.COMPLETED,
                    completion_percentage=100.0,
                    started_at=now,
                    completed_at=now,
                )
                self.db.add(rmp)
            else:
                rmp.status = ProgressStatus.COMPLETED
                rmp.completion_percentage = 100.0
                rmp.completed_at = now
                if not rmp.started_at:
                    rmp.started_at = now

            roadmap_updated = True
            logger.info(
                "Project completion auto-updated RoadmapModule '%s' to COMPLETED for student '%s'",
                project.roadmap_module_id,
                student.id,
            )

        return skills_updated, roadmap_updated
