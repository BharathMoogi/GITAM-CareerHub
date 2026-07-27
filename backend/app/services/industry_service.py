"""
Industry Intelligence Engine — Service Layer.

Provides:
- Company listing with student readiness context
- Company detail (full intelligence: skills, courses, projects, certs, interview prep)
- Readiness score calculation (5-axis: courses, projects, skills, certifications, roadmap)
- Gap analysis (what skills are missing)
- Readiness score persistence in StudentCompanyReadiness
- My readiness dashboard (student's readiness across all companies)
"""
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.company import Company
from app.models.company_mapping import CompanySkill, CompanyCourse, CompanyProject, CompanyCertification
from app.models.company_interview import CompanyInterviewRound, CompanyInterviewQuestion
from app.models.job_role import JobRole
from app.models.student import Student
from app.models.student_certification import StudentCertification
from app.models.student_company_readiness import StudentCompanyReadiness
from app.models.student_course_progress import StudentCourseProgress
from app.models.student_project import StudentProject
from app.models.student_skill import StudentSkill
from app.schemas.company import (
    CompanyCourseLinkRead,
    CompanyCertificationLinkRead,
    CompanyDetailRead,
    CompanyListRead,
    CompanyProjectLinkRead,
    CompanySkillRead,
    InterviewQuestionRead,
    InterviewRoundRead,
    JobRoleRead,
    ReadinessScoreRead,
    StudentReadinessSummaryRead,
)

logger = logging.getLogger("app.services.industry_service")

# Readiness label thresholds
_LABEL_MAP = [
    (80.0, "READY"),
    (60.0, "STRONG"),
    (40.0, "MODERATE"),
    (0.0, "WEAK"),
]


def _readiness_label(score: float) -> str:
    for threshold, label in _LABEL_MAP:
        if score >= threshold:
            return label
    return "WEAK"


def _company_load_opts():
    """Selectinload options for Company: loads all collections in separate SELECT queries."""
    return [
        selectinload(Company.job_roles),
        selectinload(Company.company_skills).selectinload(CompanySkill.skill),
        selectinload(Company.recommended_courses).selectinload(CompanyCourse.course),
        selectinload(Company.recommended_projects).selectinload(CompanyProject.project),
        selectinload(Company.recommended_certifications).selectinload(CompanyCertification.certification),
        selectinload(Company.interview_rounds),
        selectinload(Company.interview_questions).selectinload(CompanyInterviewQuestion.job_role),
    ]


class IndustryService:
    """
    Business logic for the Industry Intelligence Engine.

    Key responsibilities:
    1. List companies with per-student readiness context.
    2. Compute a 5-axis readiness score on demand (or serve cached value).
    3. Provide full company intelligence (gap analysis, interview prep, learning path).
    4. Persist and retrieve StudentCompanyReadiness records.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ─── Helpers ──────────────────────────────────────────────────────────────

    async def _get_student(self, user_id: str) -> Student:
        res = await self.db.execute(
            select(Student)
            .where(Student.user_id == user_id)
            .options(
                selectinload(Student.branch),
                selectinload(Student.user),
            )
        )
        student = res.unique().scalars().first()
        if not student:
            raise NotFoundException(message="Student profile not found.")
        return student

    async def _get_student_skills(self, student_id: str) -> Dict[str, float]:
        """Return {skill_id: score} for a student."""
        res = await self.db.execute(
            select(StudentSkill).where(StudentSkill.student_id == student_id)
        )
        rows = res.unique().scalars().all()
        return {r.skill_id: r.proficiency_score for r in rows}

    async def _compute_readiness(
        self,
        student: Student,
        company: Company,
    ) -> Tuple[float, float, float, float, float, List[str]]:
        """
        Compute (overall, course, project, skill, cert, gap_skill_names).

        Requires company to have been loaded with _company_load_opts() so that
        company.company_skills, recommended_courses, recommended_projects, and
        recommended_certifications are already populated in memory.

        Scoring axes (each 0-100):
        - Course score : % of company-recommended courses the student has COMPLETED
        - Project score: % of company-recommended projects the student has COMPLETED or IN_PROGRESS
        - Skill score  : weighted average of student skill scores vs company required skills
        - Cert score   : % of company-recommended certifications the student has COMPLETED
        - Overall      : 0.30 * course + 0.25 * project + 0.30 * skill + 0.15 * cert
        """
        student_skills = await self._get_student_skills(student.id)

        # 1 — Course score (use already-loaded collection)
        company_courses = company.recommended_courses
        course_score = 0.0
        if company_courses:
            completed = 0
            for cc in company_courses:
                cp_res = await self.db.execute(
                    select(StudentCourseProgress).where(
                        StudentCourseProgress.student_id == student.id,
                        StudentCourseProgress.course_id == cc.course_id,
                        StudentCourseProgress.status == "COMPLETED",
                    )
                )
                if cp_res.scalars().first():
                    completed += 1
            course_score = (completed / len(company_courses)) * 100.0

        # 2 — Project score (use already-loaded collection)
        company_projects = company.recommended_projects
        project_score = 0.0
        if company_projects:
            done = 0
            for cp in company_projects:
                sp_res = await self.db.execute(
                    select(StudentProject).where(
                        StudentProject.student_id == student.id,
                        StudentProject.project_id == cp.project_id,
                        StudentProject.status.in_(["COMPLETED", "IN_PROGRESS"]),
                    )
                )
                if sp_res.scalars().first():
                    done += 1
            project_score = (done / len(company_projects)) * 100.0

        # 3 — Skill score + gap analysis (use already-loaded company_skills)
        company_skill_rows = company.company_skills
        skill_score = 0.0
        gap_skill_names: List[str] = []
        if company_skill_rows:
            total_weight = sum(cs.weightage for cs in company_skill_rows)
            weighted_sum = 0.0
            for cs in company_skill_rows:
                student_score = student_skills.get(cs.skill_id, 0.0)
                threshold = {"BEGINNER": 30.0, "INTERMEDIATE": 60.0, "ADVANCED": 80.0}.get(
                    cs.required_level, 30.0
                )
                weighted_sum += (student_score / 100.0) * cs.weightage
                if student_score < threshold and cs.skill and cs.skill.name:
                    gap_skill_names.append(cs.skill.name)
            skill_score = (weighted_sum / total_weight) * 100.0 if total_weight > 0 else 0.0

        # 4 — Certification score (use already-loaded collection)
        company_certs = company.recommended_certifications
        cert_score = 0.0
        if company_certs:
            completed_certs = 0
            for cc in company_certs:
                sc_res = await self.db.execute(
                    select(StudentCertification).where(
                        StudentCertification.student_id == student.id,
                        StudentCertification.certification_id == cc.certification_id,
                        StudentCertification.status == "COMPLETED",
                    )
                )
                if sc_res.scalars().first():
                    completed_certs += 1
            cert_score = (completed_certs / len(company_certs)) * 100.0

        overall = (
            0.30 * course_score
            + 0.25 * project_score
            + 0.30 * skill_score
            + 0.15 * cert_score
        )
        return round(overall, 2), round(course_score, 2), round(project_score, 2), round(skill_score, 2), round(cert_score, 2), gap_skill_names

    async def _persist_readiness(
        self,
        student: Student,
        company: Company,
        overall: float,
        course_score: float,
        project_score: float,
        skill_score: float,
        cert_score: float,
    ) -> None:
        """Upsert a StudentCompanyReadiness record."""
        res = await self.db.execute(
            select(StudentCompanyReadiness).where(
                StudentCompanyReadiness.student_id == student.id,
                StudentCompanyReadiness.company_id == company.id,
                StudentCompanyReadiness.job_role_id.is_(None),
            )
        )
        record = res.scalars().first()
        now = datetime.now(timezone.utc)
        if record:
            record.overall_score = overall
            record.course_score = course_score
            record.project_score = project_score
            record.skill_score = skill_score
            record.certification_score = cert_score
            record.last_updated = now
        else:
            record = StudentCompanyReadiness(
                student_id=student.id,
                company_id=company.id,
                overall_score=overall,
                course_score=course_score,
                project_score=project_score,
                skill_score=skill_score,
                certification_score=cert_score,
                resume_score=0.0,
                interview_score=0.0,
                last_updated=now,
            )
            self.db.add(record)
        await self.db.commit()

    async def _load_company(self, company_id: str) -> Optional[Company]:
        """Load a single company with all collections eagerly via selectinload."""
        res = await self.db.execute(
            select(Company)
            .where(Company.id == company_id)
            .options(*_company_load_opts())
        )
        return res.unique().scalars().first()

    # ─── Public API ───────────────────────────────────────────────────────────

    async def list_companies(
        self,
        user_id: str,
        industry: Optional[str] = None,
        is_hiring: Optional[bool] = None,
        skill: Optional[str] = None,
    ) -> List[CompanyListRead]:
        """
        Return all companies with student readiness context.
        Filters: industry, is_hiring, skill name.
        """
        student = await self._get_student(user_id)
        student_skills = await self._get_student_skills(student.id)

        query = select(Company).options(*_company_load_opts())
        if industry:
            query = query.where(Company.industry.ilike(f"%{industry}%"))
        if is_hiring is not None:
            query = query.where(Company.is_hiring == is_hiring)

        res = await self.db.execute(query)
        companies = res.unique().scalars().all()

        result: List[CompanyListRead] = []
        for company in companies:
            # Optional skill filter (check company_skills)
            if skill:
                skill_names = [
                    cs.skill.name.lower() for cs in company.company_skills if cs.skill
                ]
                if not any(skill.lower() in sn for sn in skill_names):
                    continue

            overall, course_s, project_s, skill_s, cert_s, gap = await self._compute_readiness(
                student, company
            )

            # Count applied vs total skills
            company_skill_ids = {cs.skill_id for cs in company.company_skills}
            student_qualified = sum(
                1 for sk_id in company_skill_ids if student_skills.get(sk_id, 0.0) >= 30.0
            )

            top_skills = [
                CompanySkillRead(
                    skill_id=cs.skill_id,
                    skill_name=cs.skill.name if cs.skill else "Unknown",
                    skill_category=cs.skill.category if cs.skill else "Unknown",
                    required_level=cs.required_level,
                    weightage=cs.weightage,
                )
                for cs in company.company_skills[:5]
            ]

            job_roles = [
                JobRoleRead(
                    id=jr.id,
                    title=jr.title,
                    role_category=jr.role_category,
                    employment_type=jr.employment_type,
                    experience_level=jr.experience_level,
                    salary_min=jr.salary_min,
                    salary_max=jr.salary_max,
                    location=jr.location,
                    job_description=jr.job_description,
                    status=jr.status,
                )
                for jr in company.job_roles
                if jr.status == "ACTIVE"
            ]

            result.append(
                CompanyListRead(
                    id=company.id,
                    name=company.name,
                    logo=company.logo,
                    website=company.website,
                    industry=company.industry,
                    headquarters=company.headquarters,
                    description=company.description,
                    company_size=company.company_size,
                    careers_url=company.careers_url,
                    linkedin_url=company.linkedin_url,
                    glassdoor_url=company.glassdoor_url,
                    is_hiring=company.is_hiring,
                    readiness_score=overall,
                    readiness_label=_readiness_label(overall),
                    applied_skills_count=student_qualified,
                    total_skills_count=len(company_skill_ids),
                    job_roles=job_roles,
                    top_skills=top_skills,
                )
            )

        result.sort(key=lambda c: c.readiness_score, reverse=True)
        return result

    async def get_company_detail(self, user_id: str, company_id: str) -> CompanyDetailRead:
        """
        Full company intelligence for one company:
        - readiness breakdown + gap skills
        - recommended courses, projects, certifications
        - interview rounds + questions
        """
        student = await self._get_student(user_id)
        student_skills = await self._get_student_skills(student.id)

        company = await self._load_company(company_id)
        if not company:
            raise NotFoundException(message=f"Company '{company_id}' not found.")

        overall, course_s, project_s, skill_s, cert_s, gap = await self._compute_readiness(
            student, company
        )

        # Persist the score
        await self._persist_readiness(student, company, overall, course_s, project_s, skill_s, cert_s)

        # Skills
        company_skill_ids = {cs.skill_id for cs in company.company_skills}
        student_qualified = sum(
            1 for sk_id in company_skill_ids if student_skills.get(sk_id, 0.0) >= 30.0
        )
        all_skills = [
            CompanySkillRead(
                skill_id=cs.skill_id,
                skill_name=cs.skill.name if cs.skill else "Unknown",
                skill_category=cs.skill.category if cs.skill else "Unknown",
                required_level=cs.required_level,
                weightage=cs.weightage,
            )
            for cs in company.company_skills
        ]

        # Job roles
        job_roles = [
            JobRoleRead(
                id=jr.id,
                title=jr.title,
                role_category=jr.role_category,
                employment_type=jr.employment_type,
                experience_level=jr.experience_level,
                salary_min=jr.salary_min,
                salary_max=jr.salary_max,
                location=jr.location,
                job_description=jr.job_description,
                status=jr.status,
            )
            for jr in company.job_roles
        ]

        # Recommended learning
        rec_courses = [
            CompanyCourseLinkRead(
                course_id=cc.course_id,
                course_title=cc.course.title if cc.course else "Unknown",
                difficulty=cc.course.difficulty if cc.course else "BEGINNER",
                estimated_hours=cc.course.estimated_hours if cc.course else None,
                importance=cc.importance,
            )
            for cc in company.recommended_courses
        ]
        rec_projects = [
            CompanyProjectLinkRead(
                project_id=cp.project_id,
                project_title=cp.project.title if cp.project else "Unknown",
                difficulty=cp.project.difficulty if cp.project else "BEGINNER",
                project_type=cp.project.project_type if cp.project else "MINI",
                importance=cp.importance,
            )
            for cp in company.recommended_projects
        ]
        rec_certs = [
            CompanyCertificationLinkRead(
                certification_id=cc.certification_id,
                certification_title=cc.certification.title if cc.certification else "Unknown",
                provider=cc.certification.provider if cc.certification else "Unknown",
                difficulty=cc.certification.difficulty if cc.certification else "BEGINNER",
                importance=cc.importance,
            )
            for cc in company.recommended_certifications
        ]

        # Interview prep
        rounds = [
            InterviewRoundRead(
                id=ir.id,
                round_name=ir.round_name,
                round_order=ir.round_order,
                description=ir.description,
            )
            for ir in sorted(company.interview_rounds, key=lambda x: x.round_order)
        ]
        questions = [
            InterviewQuestionRead(
                id=iq.id,
                question=iq.question,
                difficulty=iq.difficulty,
                expected_answer=iq.expected_answer,
                category=iq.category,
                job_role_title=iq.job_role.title if iq.job_role else None,
            )
            for iq in company.interview_questions
        ]

        return CompanyDetailRead(
            id=company.id,
            name=company.name,
            logo=company.logo,
            website=company.website,
            industry=company.industry,
            headquarters=company.headquarters,
            description=company.description,
            company_size=company.company_size,
            careers_url=company.careers_url,
            linkedin_url=company.linkedin_url,
            glassdoor_url=company.glassdoor_url,
            is_hiring=company.is_hiring,
            readiness_score=overall,
            readiness_label=_readiness_label(overall),
            applied_skills_count=student_qualified,
            total_skills_count=len(company_skill_ids),
            job_roles=job_roles,
            top_skills=all_skills,
            course_score=course_s,
            project_score=project_s,
            skill_score=skill_s,
            certification_score=cert_s,
            gap_skills=gap,
            recommended_courses=rec_courses,
            recommended_projects=rec_projects,
            recommended_certifications=rec_certs,
            interview_rounds=rounds,
            interview_questions=questions,
        )

    async def get_my_readiness(self, user_id: str) -> StudentReadinessSummaryRead:
        """
        Return a readiness dashboard for the authenticated student:
        - Average readiness score across all assessed companies
        - Top company name
        - Per-company readiness breakdown
        """
        student = await self._get_student(user_id)

        # Fetch existing readiness records (with company eager loaded)
        rr_res = await self.db.execute(
            select(StudentCompanyReadiness)
            .where(
                StudentCompanyReadiness.student_id == student.id,
                StudentCompanyReadiness.job_role_id.is_(None),
            )
            .options(
                selectinload(StudentCompanyReadiness.company)
            )
        )
        records = rr_res.unique().scalars().all()

        # If no records yet, compute for all companies (eager init)
        if not records:
            c_res = await self.db.execute(
                select(Company).options(*_company_load_opts())
            )
            all_companies = c_res.unique().scalars().all()
            for company in all_companies:
                overall, cs, ps, ss, cert_s, _ = await self._compute_readiness(student, company)
                await self._persist_readiness(student, company, overall, cs, ps, ss, cert_s)
            # Re-fetch
            rr_res = await self.db.execute(
                select(StudentCompanyReadiness)
                .where(
                    StudentCompanyReadiness.student_id == student.id,
                    StudentCompanyReadiness.job_role_id.is_(None),
                )
                .options(selectinload(StudentCompanyReadiness.company))
            )
            records = rr_res.unique().scalars().all()

        # Build the readiness items
        readiness_items: List[ReadinessScoreRead] = []
        for rec in records:
            company = rec.company
            if not company:
                continue
            # Re-load company with full eager options for readiness computation
            full_company = await self._load_company(company.id)
            if not full_company:
                continue
            _, _, _, _, _, gap = await self._compute_readiness(student, full_company)
            readiness_items.append(
                ReadinessScoreRead(
                    company_id=company.id,
                    company_name=company.name,
                    company_logo=company.logo,
                    industry=company.industry,
                    overall_score=rec.overall_score,
                    course_score=rec.course_score,
                    project_score=rec.project_score,
                    skill_score=rec.skill_score,
                    certification_score=rec.certification_score,
                    readiness_label=_readiness_label(rec.overall_score),
                    gap_skills=gap,
                    last_updated=rec.last_updated,
                )
            )

        readiness_items.sort(key=lambda x: x.overall_score, reverse=True)
        avg = sum(r.overall_score for r in readiness_items) / len(readiness_items) if readiness_items else 0.0
        top = readiness_items[0] if readiness_items else None

        branch_name = student.branch.name if student.branch else "Unknown"
        student_name = student.full_name or (student.user.email if student.user else "Student")

        return StudentReadinessSummaryRead(
            student_id=student.id,
            student_name=student_name,
            branch_name=branch_name,
            current_semester=student.semester,
            average_readiness=round(avg, 2),
            top_company=top.company_name if top else None,
            top_company_score=top.overall_score if top else 0.0,
            companies=readiness_items,
        )
