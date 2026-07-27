import logging
from collections import Counter
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.models.course import Course
from app.models.course_skill import CourseSkill
from app.models.roadmap import Roadmap
from app.models.roadmap_module import RoadmapModule
from app.models.roadmap_dependency import RoadmapModuleDependency
from app.models.skill import Skill
from app.models.student import Student
from app.models.student_course_progress import StudentCourseProgress
from app.models.student_progress import StudentRoadmapProgress
from app.models.student_skill import StudentSkill
from app.schemas.course import (
    CourseDetailRead,
    CourseListRead,
    CourseProgressRead,
    CourseSkillRead,
    CourseOutcomeRead,
    CourseResourceRead,
    SkillDashboardRead,
    StudentSkillRead,
    UpdateCourseProgressRequest,
)
from app.schemas.roadmap import ProgressStatus

logger = logging.getLogger("app.services.course_service")

ALLOWED_COURSE_STATUSES = ["IN_PROGRESS", "COMPLETED"]


class CourseService:
    """
    Business logic for the Learning Engine.
    Handles course listing, lock checks, progress updates, and skill calculation.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ─── Internal Helpers ──────────────────────────────────────────────────────

    async def _get_student(self, user_id: str) -> Student:
        res = await self.db.execute(select(Student).where(Student.user_id == user_id))
        student = res.unique().scalars().first()
        if not student:
            raise NotFoundException(message="Student profile not found.")
        return student

    async def _get_student_course_progress_map(
        self, student_id: str
    ) -> Dict[str, StudentCourseProgress]:
        res = await self.db.execute(
            select(StudentCourseProgress).where(StudentCourseProgress.student_id == student_id)
        )
        rows = res.unique().scalars().all()
        return {r.course_id: r for r in rows}

    async def _get_student_skill_map(
        self, student_id: str
    ) -> Dict[str, StudentSkill]:
        res = await self.db.execute(
            select(StudentSkill).where(StudentSkill.student_id == student_id)
        )
        rows = res.unique().scalars().all()
        return {r.skill_id: r for r in rows}

    async def _resolve_course_lock(
        self,
        course: Course,
        student: Student,
        course_progress_map: Dict[str, StudentCourseProgress],
    ) -> tuple[bool, Optional[str]]:
        """
        Determine lock status for a course.
        Rule 1: If course is in a future semester → locked.
        Rule 2: If linked to a RoadmapModule that is locked by the Roadmap Engine → locked.
        """
        # Rule 1 — Future semester
        if course.semester.semester_number > student.semester:
            return True, (
                f"Future semester locked "
                f"(Semester {course.semester.semester_number} requires completion of Semester {student.semester})"
            )

        # Rule 2 — Roadmap Engine lock check (via linked module)
        if course.roadmap_module_id:
            module = await self.db.get(RoadmapModule, course.roadmap_module_id)
            if module:
                roadmap = await self.db.get(Roadmap, module.roadmap_id)
                if roadmap:
                    # Check if all module prerequisites are completed
                    dep_res = await self.db.execute(
                        select(RoadmapModuleDependency).where(
                            RoadmapModuleDependency.module_id == module.id
                        )
                    )
                    deps = dep_res.unique().scalars().all()
                    for dep in deps:
                        prog_res = await self.db.execute(
                            select(StudentRoadmapProgress).where(
                                StudentRoadmapProgress.roadmap_module_id == dep.depends_on_module_id
                            )
                        )
                        prog = prog_res.unique().scalars().first()
                        if not prog or prog.status not in (ProgressStatus.COMPLETED, ProgressStatus.SKIPPED):
                            prereq_module = await self.db.get(RoadmapModule, dep.depends_on_module_id)
                            prereq_name = prereq_module.module_name if prereq_module else dep.depends_on_module_id
                            return True, f"Prerequisite not completed: '{prereq_name}'"

        return False, None

    def _build_course_list_item(
        self,
        course: Course,
        progress_map: Dict[str, StudentCourseProgress],
        is_locked: bool,
        lock_reason: Optional[str],
    ) -> CourseListRead:
        prog = progress_map.get(course.id)
        return CourseListRead(
            id=course.id,
            title=course.title,
            description=course.description,
            branch_id=course.branch_id,
            branch_name=course.branch.name,
            academic_year_id=course.academic_year_id,
            year_number=course.academic_year.year_number,
            semester_id=course.semester_id,
            semester_number=course.semester.semester_number,
            difficulty=course.difficulty,
            estimated_hours=course.estimated_hours,
            thumbnail=course.thumbnail,
            status=course.status,
            is_locked=is_locked,
            lock_reason=lock_reason,
            user_status=prog.status if prog else "NOT_STARTED",
            completion_percentage=prog.completion_percentage if prog else 0.0,
            skills=[
                CourseSkillRead(
                    skill_id=cs.skill_id,
                    skill_name=cs.skill.name,
                    skill_category=cs.skill.category,
                    proficiency_level=cs.proficiency_level,
                )
                for cs in course.course_skills
            ],
        )

    def _build_course_detail(
        self,
        course: Course,
        progress_map: Dict[str, StudentCourseProgress],
        is_locked: bool,
        lock_reason: Optional[str],
    ) -> CourseDetailRead:
        base = self._build_course_list_item(course, progress_map, is_locked, lock_reason)
        return CourseDetailRead(
            **base.model_dump(),
            learning_objectives=course.learning_objectives,
            prerequisites=course.prerequisites,
            resources=[
                CourseResourceRead(
                    id=r.id, resource_type=r.resource_type, title=r.title,
                    url=r.url, provider=r.provider, display_order=r.display_order,
                    duration=r.duration,
                )
                for r in sorted(course.resources, key=lambda x: x.display_order)
            ],
            outcomes=[
                CourseOutcomeRead(
                    id=o.id, title=o.title, description=o.description,
                    display_order=o.display_order,
                )
                for o in sorted(course.outcomes, key=lambda x: x.display_order)
            ],
        )

    # ─── Public API Methods ────────────────────────────────────────────────────

    async def list_courses(
        self,
        user_id: str,
        branch: Optional[str] = None,
        year: Optional[int] = None,
        semester: Optional[int] = None,
        difficulty: Optional[str] = None,
        skill_name: Optional[str] = None,
    ) -> List[CourseListRead]:
        """
        Returns published courses for the student's branch with lock and progress state.
        Supports optional filters: branch, year, semester, difficulty, skill name.
        """
        student = await self._get_student(user_id)

        query = select(Course).where(Course.status == "PUBLISHED")

        # Filter by branch — default to student's branch if not specified
        if branch:
            branch_res = await self.db.execute(
                select(Course.branch_id).where(Course.branch_id == student.branch_id).limit(1)
            )
        query = query.where(Course.branch_id == student.branch_id)

        result = await self.db.execute(query)
        courses: List[Course] = result.unique().scalars().all()

        # Apply post-load filters
        if year:
            courses = [c for c in courses if c.academic_year.year_number == year]
        if semester:
            courses = [c for c in courses if c.semester.semester_number == semester]
        if difficulty:
            courses = [c for c in courses if c.difficulty.upper() == difficulty.upper()]
        if skill_name:
            skill_name_lower = skill_name.lower()
            courses = [
                c for c in courses
                if any(cs.skill.name.lower() == skill_name_lower for cs in c.course_skills)
            ]

        # Sort by year → semester → difficulty
        difficulty_order = {"BEGINNER": 1, "INTERMEDIATE": 2, "ADVANCED": 3}
        courses.sort(key=lambda c: (
            c.academic_year.year_number,
            c.semester.semester_number,
            difficulty_order.get(c.difficulty, 99),
        ))

        progress_map = await self._get_student_course_progress_map(student.id)

        output = []
        for course in courses:
            is_locked, lock_reason = await self._resolve_course_lock(course, student, progress_map)
            output.append(self._build_course_list_item(course, progress_map, is_locked, lock_reason))
        return output

    async def get_course_detail(self, user_id: str, course_id: str) -> CourseDetailRead:
        """Returns full course detail with resources, outcomes, skills, and student progress."""
        student = await self._get_student(user_id)

        result = await self.db.execute(select(Course).where(Course.id == course_id))
        course = result.unique().scalars().first()
        if not course:
            raise NotFoundException(message=f"Course '{course_id}' not found.")

        progress_map = await self._get_student_course_progress_map(student.id)
        is_locked, lock_reason = await self._resolve_course_lock(course, student, progress_map)

        return self._build_course_detail(course, progress_map, is_locked, lock_reason)

    async def update_course_progress(
        self,
        user_id: str,
        course_id: str,
        payload: UpdateCourseProgressRequest,
    ) -> CourseProgressRead:
        """
        Update student course progress.
        On COMPLETED:
          1. Upserts StudentCourseProgress.
          2. Updates StudentSkill scores for all skills linked to the course.
          3. Updates linked StudentRoadmapProgress (if roadmap_module_id is set).
        """
        if payload.status not in ALLOWED_COURSE_STATUSES:
            raise BadRequestException(
                message=f"Invalid status '{payload.status}'. Allowed: {', '.join(ALLOWED_COURSE_STATUSES)}"
            )

        student = await self._get_student(user_id)

        result = await self.db.execute(select(Course).where(Course.id == course_id))
        course = result.unique().scalars().first()
        if not course:
            raise NotFoundException(message=f"Course '{course_id}' not found.")

        # Check course is not locked
        progress_map = await self._get_student_course_progress_map(student.id)
        is_locked, lock_reason = await self._resolve_course_lock(course, student, progress_map)
        if is_locked:
            raise BadRequestException(
                message=f"Cannot update progress — course is locked: {lock_reason}"
            )

        now = datetime.now(timezone.utc)

        # ── 1. Upsert StudentCourseProgress ──────────────────────────────────
        existing_prog = progress_map.get(course_id)
        if not existing_prog:
            existing_prog = StudentCourseProgress(
                student_id=student.id,
                course_id=course_id,
                status=payload.status,
                completion_percentage=0.0,
            )
            self.db.add(existing_prog)

        existing_prog.status = payload.status
        if payload.completion_percentage is not None:
            existing_prog.completion_percentage = payload.completion_percentage
        elif payload.status == "COMPLETED":
            existing_prog.completion_percentage = 100.0
        elif payload.status == "IN_PROGRESS" and existing_prog.completion_percentage == 0.0:
            existing_prog.completion_percentage = 10.0

        if payload.status == "IN_PROGRESS" and not existing_prog.started_at:
            existing_prog.started_at = now
        if payload.status == "COMPLETED":
            existing_prog.completed_at = now
            if not existing_prog.started_at:
                existing_prog.started_at = now

        await self.db.flush()

        # ── 2. Update StudentSkill scores (on COMPLETED) ─────────────────────
        skills_updated: List[StudentSkillRead] = []
        roadmap_module_updated = False

        if payload.status == "COMPLETED":
            skill_map = await self._get_student_skill_map(student.id)

            # Load skill proficiency_level -> score mapping
            proficiency_score_map = {"BEGINNER": 25.0, "INTERMEDIATE": 50.0, "ADVANCED": 80.0}

            for cs in course.course_skills:
                score_increment = proficiency_score_map.get(cs.proficiency_level, 25.0)
                existing_sk = skill_map.get(cs.skill_id)
                if existing_sk:
                    # Average the new score with existing score (capped at 100)
                    existing_sk.proficiency_score = min(
                        100.0, (existing_sk.proficiency_score + score_increment) / 2.0
                        if existing_sk.proficiency_score > 0
                        else score_increment
                    )
                    existing_sk.earned_from_course_id = course_id
                    existing_sk.last_updated = now
                else:
                    existing_sk = StudentSkill(
                        student_id=student.id,
                        skill_id=cs.skill_id,
                        proficiency_score=score_increment,
                        earned_from_course_id=course_id,
                        last_updated=now,
                    )
                    self.db.add(existing_sk)
                    await self.db.flush()
                    skill_map[cs.skill_id] = existing_sk

                skills_updated.append(StudentSkillRead(
                    id=existing_sk.id,
                    skill_id=cs.skill_id,
                    skill_name=cs.skill.name,
                    skill_category=cs.skill.category,
                    proficiency_score=existing_sk.proficiency_score,
                    earned_from_course_id=course_id,
                    earned_from_course_title=course.title,
                    last_updated=existing_sk.last_updated,
                ))

            # ── 3. Update linked RoadmapModule progress ───────────────────────
            if course.roadmap_module_id:
                rmp_res = await self.db.execute(
                    select(StudentRoadmapProgress).where(
                        StudentRoadmapProgress.student_id == student.id,
                        StudentRoadmapProgress.roadmap_module_id == course.roadmap_module_id,
                    )
                )
                rmp = rmp_res.unique().scalars().first()
                if not rmp:
                    rmp = StudentRoadmapProgress(
                        student_id=student.id,
                        roadmap_module_id=course.roadmap_module_id,
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
                roadmap_module_updated = True
                logger.info(
                    "Auto-updated RoadmapModule '%s' to COMPLETED for student '%s'",
                    course.roadmap_module_id, student.id,
                )

        await self.db.commit()
        await self.db.refresh(existing_prog)

        return CourseProgressRead(
            course_id=course_id,
            course_title=course.title,
            status=existing_prog.status,
            completion_percentage=existing_prog.completion_percentage,
            started_at=existing_prog.started_at,
            completed_at=existing_prog.completed_at,
            skills_updated=skills_updated,
            roadmap_module_updated=roadmap_module_updated,
        )

    async def get_student_skills(self, user_id: str) -> SkillDashboardRead:
        """Returns full student skill dashboard with proficiency scores and source courses."""
        student = await self._get_student(user_id)

        res = await self.db.execute(
            select(StudentSkill).where(StudentSkill.student_id == student.id)
        )
        student_skills = res.unique().scalars().all()

        skills_read = []
        for ss in student_skills:
            earned_title = None
            if ss.earned_from_course_id:
                c_res = await self.db.execute(
                    select(Course.title).where(Course.id == ss.earned_from_course_id)
                )
                earned_title = c_res.scalar_one_or_none()

            skills_read.append(StudentSkillRead(
                id=ss.id,
                skill_id=ss.skill_id,
                skill_name=ss.skill.name,
                skill_category=ss.skill.category,
                proficiency_score=ss.proficiency_score,
                earned_from_course_id=ss.earned_from_course_id,
                earned_from_course_title=earned_title,
                last_updated=ss.last_updated,
            ))

        # Sort by highest proficiency score
        skills_read.sort(key=lambda s: s.proficiency_score, reverse=True)

        avg_score = (
            round(sum(s.proficiency_score for s in skills_read) / len(skills_read), 2)
            if skills_read else 0.0
        )

        # Compute top category
        category_counts = Counter(s.skill_category for s in skills_read)
        top_category = category_counts.most_common(1)[0][0] if category_counts else None

        return SkillDashboardRead(
            total_skills_earned=len(skills_read),
            average_proficiency_score=avg_score,
            top_category=top_category,
            skills=skills_read,
        )
