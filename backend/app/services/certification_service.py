import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.certification import Certification
from app.models.certification_skill import CertificationPrerequisite
from app.models.course import Course
from app.models.project import Project
from app.models.roadmap import Roadmap
from app.models.roadmap_module import RoadmapModule
from app.models.roadmap_dependency import RoadmapModuleDependency
from app.models.student import Student
from app.models.student_certification import StudentCertification
from app.models.student_course_progress import StudentCourseProgress
from app.models.student_project import StudentProject
from app.models.student_progress import StudentRoadmapProgress
from app.models.student_skill import StudentSkill
from app.schemas.certification import (
    CertificationBenefitRead,
    CertificationDetailRead,
    CertificationExamRead,
    CertificationListRead,
    CertificationPrerequisiteRead,
    CertificationProgressRead,
    CertificationSkillRead,
    StudentCertificationRead,
    SubmitCertificationRequest,
    UpdateCertificationProgressRequest,
)
from app.schemas.roadmap import ProgressStatus

logger = logging.getLogger("app.services.certification_service")

ALLOWED_CERT_PROGRESS_STATUSES = ["IN_PROGRESS", "COMPLETED"]


class CertificationService:
    """
    Business logic for the Certification Intelligence Engine.
    Handles certification listings, 5-way lock checks, progress updates, submission,
    skill score boosts, placement readiness calculations, and roadmap/internship cascades.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_student(self, user_id: str) -> Student:
        res = await self.db.execute(select(Student).where(Student.user_id == user_id))
        student = res.unique().scalars().first()
        if not student:
            raise NotFoundException(message="Student profile not found.")
        return student

    async def _get_student_cert_map(self, student_id: str) -> Dict[str, StudentCertification]:
        res = await self.db.execute(
            select(StudentCertification).where(StudentCertification.student_id == student_id)
        )
        rows = res.unique().scalars().all()
        return {r.certification_id: r for r in rows}

    async def _resolve_certification_lock(
        self,
        cert: Certification,
        student: Student,
    ) -> Tuple[bool, Optional[str]]:
        """
        Students can ONLY start/submit certifications after:
        1. Semester check (not in future semester).
        2. Required courses in the branch/semester are COMPLETED.
        3. Required projects in the branch/semester are COMPLETED.
        4. Required minimum skill scores are achieved in StudentSkill.
        5. Linked RoadmapModule prerequisite dependencies are COMPLETED.
        """
        # Rule 1 — Semester boundary
        if cert.semester.semester_number > student.semester:
            return True, (
                f"Future semester locked "
                f"(Semester {cert.semester.semester_number} requires completion of Semester {student.semester})"
            )

        # Rule 2 — Required courses completed
        course_res = await self.db.execute(
            select(Course).where(
                Course.branch_id == cert.branch_id,
                Course.semester_id == cert.semester_id,
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

        # Rule 3 — Required projects completed
        proj_res = await self.db.execute(
            select(Project).where(
                Project.branch_id == cert.branch_id,
                Project.semester_id == cert.semester_id,
                Project.status == "PUBLISHED",
            )
        )
        required_projects = proj_res.unique().scalars().all()
        for proj in required_projects:
            sp_res = await self.db.execute(
                select(StudentProject).where(
                    StudentProject.student_id == student.id,
                    StudentProject.project_id == proj.id,
                )
            )
            sp = sp_res.unique().scalars().first()
            if not sp or sp.status not in ("COMPLETED", "SUBMITTED"):
                return True, f"Required project not completed: '{proj.title}'"

        # Rule 4 — Explicit prerequisites & minimum skill scores
        for prereq in cert.prerequisites:
            if prereq.required_course_id:
                c_prog = await self.db.execute(
                    select(StudentCourseProgress).where(
                        StudentCourseProgress.student_id == student.id,
                        StudentCourseProgress.course_id == prereq.required_course_id,
                    )
                )
                cp = c_prog.unique().scalars().first()
                if not cp or cp.status != "COMPLETED":
                    c_obj = await self.db.get(Course, prereq.required_course_id)
                    c_title = c_obj.title if c_obj else prereq.required_course_id
                    return True, f"Prerequisite course not completed: '{c_title}'"

            if prereq.required_project_id:
                p_prog = await self.db.execute(
                    select(StudentProject).where(
                        StudentProject.student_id == student.id,
                        StudentProject.project_id == prereq.required_project_id,
                    )
                )
                pp = p_prog.unique().scalars().first()
                if not pp or pp.status not in ("COMPLETED", "SUBMITTED"):
                    p_obj = await self.db.get(Project, prereq.required_project_id)
                    p_title = p_obj.title if p_obj else prereq.required_project_id
                    return True, f"Prerequisite project not completed: '{p_title}'"

            if prereq.minimum_skill_score:
                # Check all cert skills meet the score
                for cs in cert.certification_skills:
                    ss_res = await self.db.execute(
                        select(StudentSkill).where(
                            StudentSkill.student_id == student.id,
                            StudentSkill.skill_id == cs.skill_id,
                        )
                    )
                    ss = ss_res.unique().scalars().first()
                    if not ss or ss.proficiency_score < prereq.minimum_skill_score:
                        return True, f"Skill score for '{cs.skill.name}' ({ss.proficiency_score if ss else 0}) below required {prereq.minimum_skill_score}"

        # Rule 5 — Roadmap Module unlock check
        if cert.roadmap_module_id:
            module = await self.db.get(RoadmapModule, cert.roadmap_module_id)
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

    def _build_certification_list_item(
        self,
        cert: Certification,
        sc: Optional[StudentCertification],
        is_locked: bool,
        lock_reason: Optional[str],
    ) -> CertificationListRead:
        return CertificationListRead(
            id=cert.id,
            title=cert.title,
            provider=cert.provider,
            provider_type=cert.provider_type,
            description=cert.description,
            official_url=cert.official_url,
            difficulty=cert.difficulty,
            estimated_hours=cert.estimated_hours,
            branch_id=cert.branch_id,
            branch_name=cert.branch.name,
            year_number=cert.academic_year.year_number,
            semester_number=cert.semester.semester_number,
            certificate_type=cert.certificate_type,
            thumbnail=cert.thumbnail,
            status=cert.status,
            is_locked=is_locked,
            lock_reason=lock_reason,
            user_status=sc.status if sc else "NOT_STARTED",
            verified=sc.verified if sc else False,
            skills=[
                CertificationSkillRead(
                    skill_id=cs.skill_id,
                    skill_name=cs.skill.name,
                    skill_category=cs.skill.category,
                    required_level=cs.required_level,
                )
                for cs in cert.certification_skills
            ],
        )

    def _build_certification_detail(
        self,
        cert: Certification,
        sc: Optional[StudentCertification],
        is_locked: bool,
        lock_reason: Optional[str],
    ) -> CertificationDetailRead:
        base = self._build_certification_list_item(cert, sc, is_locked, lock_reason)
        return CertificationDetailRead(
            **base.model_dump(),
            prerequisites=[
                CertificationPrerequisiteRead(
                    id=pr.id,
                    required_course_id=pr.required_course_id,
                    required_course_title=pr.required_course.title if pr.required_course else None,
                    required_project_id=pr.required_project_id,
                    required_project_title=pr.required_project.title if pr.required_project else None,
                    minimum_skill_score=pr.minimum_skill_score,
                )
                for pr in cert.prerequisites
            ],
            exams=[
                CertificationExamRead(
                    id=ex.id,
                    exam_name=ex.exam_name,
                    exam_duration=ex.exam_duration,
                    passing_score=ex.passing_score,
                    exam_pattern=ex.exam_pattern,
                    official_link=ex.official_link,
                )
                for ex in cert.exams
            ],
            benefits=[
                CertificationBenefitRead(
                    id=b.id, benefit=b.benefit, display_order=b.display_order
                )
                for b in sorted(cert.benefits, key=lambda x: x.display_order)
            ],
            certificate_url=sc.certificate_url if sc else None,
            verification_id=sc.verification_id if sc else None,
            issue_date=sc.issue_date if sc else None,
            expiry_date=sc.expiry_date if sc else None,
            score=sc.score if sc else None,
        )

    # ─── Public API Methods ────────────────────────────────────────────────────

    async def list_certifications(
        self,
        user_id: str,
        branch: Optional[str] = None,
        semester: Optional[int] = None,
        difficulty: Optional[str] = None,
        provider: Optional[str] = None,
        skill: Optional[str] = None,
    ) -> List[CertificationListRead]:
        student = await self._get_student(user_id)

        query = select(Certification).where(Certification.status == "PUBLISHED")
        query = query.where(Certification.branch_id == student.branch_id)

        res = await self.db.execute(query)
        certs: List[Certification] = res.unique().scalars().all()

        if semester:
            certs = [c for c in certs if c.semester.semester_number == semester]
        if difficulty:
            certs = [c for c in certs if c.difficulty.upper() == difficulty.upper()]
        if provider:
            prov_lower = provider.lower()
            certs = [c for c in certs if c.provider.lower() == prov_lower or c.provider_type.lower() == prov_lower]
        if skill:
            skill_lower = skill.lower()
            certs = [
                c for c in certs
                if any(cs.skill.name.lower() == skill_lower for cs in c.certification_skills)
            ]

        sc_map = await self._get_student_cert_map(student.id)

        output = []
        for cert in certs:
            is_locked, lock_reason = await self._resolve_certification_lock(cert, student)
            sc = sc_map.get(cert.id)
            output.append(self._build_certification_list_item(cert, sc, is_locked, lock_reason))

        return output

    async def get_certification_detail(self, user_id: str, certification_id: str) -> CertificationDetailRead:
        student = await self._get_student(user_id)

        res = await self.db.execute(select(Certification).where(Certification.id == certification_id))
        cert = res.unique().scalars().first()
        if not cert:
            raise NotFoundException(message=f"Certification '{certification_id}' not found.")

        sc_map = await self._get_student_cert_map(student.id)
        sc = sc_map.get(cert.id)
        is_locked, lock_reason = await self._resolve_certification_lock(cert, student)

        return self._build_certification_detail(cert, sc, is_locked, lock_reason)

    async def update_certification_progress(
        self,
        user_id: str,
        certification_id: str,
        payload: UpdateCertificationProgressRequest,
    ) -> CertificationProgressRead:
        if payload.status not in ALLOWED_CERT_PROGRESS_STATUSES:
            raise BadRequestException(
                message=f"Invalid status '{payload.status}'. Allowed: {', '.join(ALLOWED_CERT_PROGRESS_STATUSES)}"
            )

        student = await self._get_student(user_id)

        res = await self.db.execute(select(Certification).where(Certification.id == certification_id))
        cert = res.unique().scalars().first()
        if not cert:
            raise NotFoundException(message=f"Certification '{certification_id}' not found.")

        is_locked, lock_reason = await self._resolve_certification_lock(cert, student)
        if is_locked:
            raise BadRequestException(message=f"Cannot update progress — certification is locked: {lock_reason}")

        sc_map = await self._get_student_cert_map(student.id)
        sc = sc_map.get(certification_id)
        now = datetime.now(timezone.utc)

        if not sc:
            sc = StudentCertification(
                student_id=student.id,
                certification_id=certification_id,
                status=payload.status,
            )
            self.db.add(sc)

        sc.status = payload.status
        if payload.status == "IN_PROGRESS" and not sc.started_at:
            sc.started_at = now
        elif payload.status == "COMPLETED":
            sc.completed_at = now
            sc.verified = True
            if not sc.started_at:
                sc.started_at = now

        skills_updated = []
        roadmap_updated = False
        placement_score = 0.0
        internship_unlocked = False

        if payload.status == "COMPLETED":
            skills_updated, roadmap_updated, placement_score, internship_unlocked = await self._process_completion_rewards(student, cert, now)

        await self.db.commit()
        await self.db.refresh(sc)

        return CertificationProgressRead(
            certification_id=certification_id,
            certification_title=cert.title,
            status=sc.status,
            certificate_url=sc.certificate_url,
            verification_id=sc.verification_id,
            issue_date=sc.issue_date,
            score=sc.score,
            verified=sc.verified,
            skills_updated=skills_updated,
            roadmap_module_updated=roadmap_updated,
            placement_readiness_score=placement_score,
            internship_unlocked=internship_unlocked,
        )

    async def submit_certification(
        self,
        user_id: str,
        certification_id: str,
        payload: SubmitCertificationRequest,
    ) -> CertificationProgressRead:
        student = await self._get_student(user_id)

        res = await self.db.execute(select(Certification).where(Certification.id == certification_id))
        cert = res.unique().scalars().first()
        if not cert:
            raise NotFoundException(message=f"Certification '{certification_id}' not found.")

        is_locked, lock_reason = await self._resolve_certification_lock(cert, student)
        if is_locked:
            raise BadRequestException(message=f"Cannot submit — certification is locked: {lock_reason}")

        sc_map = await self._get_student_cert_map(student.id)
        sc = sc_map.get(certification_id)
        now = datetime.now(timezone.utc)

        if not sc:
            sc = StudentCertification(
                student_id=student.id,
                certification_id=certification_id,
                status="COMPLETED",
            )
            self.db.add(sc)

        sc.status = "COMPLETED"
        sc.certificate_url = payload.certificate_url
        sc.verification_id = payload.verification_id
        sc.score = payload.score
        sc.issue_date = payload.issue_date or now
        sc.expiry_date = payload.expiry_date
        sc.verified = True
        sc.completed_at = now
        if not sc.started_at:
            sc.started_at = now

        skills_updated, roadmap_updated, placement_score, internship_unlocked = await self._process_completion_rewards(student, cert, now)

        await self.db.commit()
        await self.db.refresh(sc)

        return CertificationProgressRead(
            certification_id=certification_id,
            certification_title=cert.title,
            status=sc.status,
            certificate_url=sc.certificate_url,
            verification_id=sc.verification_id,
            issue_date=sc.issue_date,
            score=sc.score,
            verified=sc.verified,
            skills_updated=skills_updated,
            roadmap_module_updated=roadmap_updated,
            placement_readiness_score=placement_score,
            internship_unlocked=internship_unlocked,
        )

    async def get_my_certifications(self, user_id: str) -> List[StudentCertificationRead]:
        student = await self._get_student(user_id)

        res = await self.db.execute(
            select(StudentCertification).where(StudentCertification.student_id == student.id)
        )
        scs = res.unique().scalars().all()

        output = []
        for sc in scs:
            c = sc.certification
            output.append(
                StudentCertificationRead(
                    id=sc.id,
                    certification_id=c.id,
                    certification_title=c.title,
                    provider=c.provider,
                    provider_type=c.provider_type,
                    difficulty=c.difficulty,
                    branch_name=c.branch.name,
                    year_number=c.academic_year.year_number,
                    semester_number=c.semester.semester_number,
                    status=sc.status,
                    certificate_url=sc.certificate_url,
                    verification_id=sc.verification_id,
                    issue_date=sc.issue_date,
                    expiry_date=sc.expiry_date,
                    score=sc.score,
                    verified=sc.verified,
                    started_at=sc.started_at,
                    completed_at=sc.completed_at,
                )
            )

        output.sort(key=lambda x: x.completed_at or datetime.min, reverse=True)
        return output

    async def _process_completion_rewards(
        self, student: Student, cert: Certification, now: datetime
    ) -> Tuple[List[dict], bool, float, bool]:
        skills_updated = []
        roadmap_updated = False
        internship_unlocked = False

        # 1. Update Student Skills
        boost_map = {"BEGINNER": 20.0, "INTERMEDIATE": 35.0, "ADVANCED": 50.0}
        score_boost = boost_map.get(cert.difficulty, 25.0)

        for cs in cert.certification_skills:
            ss_res = await self.db.execute(
                select(StudentSkill).where(
                    StudentSkill.student_id == student.id,
                    StudentSkill.skill_id == cs.skill_id,
                )
            )
            ss = ss_res.unique().scalars().first()
            if ss:
                ss.proficiency_score = min(100.0, ss.proficiency_score + score_boost)
                ss.last_updated = now
            else:
                ss = StudentSkill(
                    student_id=student.id,
                    skill_id=cs.skill_id,
                    proficiency_score=score_boost,
                    earned_from_course_id=None,
                    last_updated=now,
                )
                self.db.add(ss)
                await self.db.flush()

            skills_updated.append(
                {
                    "skill_id": cs.skill_id,
                    "skill_name": cs.skill.name,
                    "new_score": ss.proficiency_score,
                }
            )

        # 2. Update StudentRoadmapProgress & unlock dependent Internship module
        if cert.roadmap_module_id:
            rmp_res = await self.db.execute(
                select(StudentRoadmapProgress).where(
                    StudentRoadmapProgress.student_id == student.id,
                    StudentRoadmapProgress.roadmap_module_id == cert.roadmap_module_id,
                )
            )
            rmp = rmp_res.unique().scalars().first()
            if not rmp:
                rmp = StudentRoadmapProgress(
                    student_id=student.id,
                    roadmap_module_id=cert.roadmap_module_id,
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
            internship_unlocked = True
            logger.info(
                "Certification completed — auto-updated RoadmapModule '%s' to COMPLETED and unlocked Internship module for student '%s'",
                cert.roadmap_module_id,
                student.id,
            )

        # 3. Calculate Placement Readiness Score
        # Formula: Base 40% from completed certs + average skill score (60% weight)
        sc_count_res = await self.db.execute(
            select(StudentCertification).where(
                StudentCertification.student_id == student.id,
                StudentCertification.status == "COMPLETED",
            )
        )
        completed_certs_count = len(sc_count_res.unique().scalars().all()) + 1

        all_ss_res = await self.db.execute(
            select(StudentSkill).where(StudentSkill.student_id == student.id)
        )
        all_skills = all_ss_res.unique().scalars().all()
        avg_skill_score = (
            sum(s.proficiency_score for s in all_skills) / len(all_skills)
            if all_skills else 0.0
        )

        placement_readiness_score = min(
            100.0, round((completed_certs_count * 15.0) + (avg_skill_score * 0.6), 2)
        )

        return skills_updated, roadmap_updated, placement_readiness_score, internship_unlocked
