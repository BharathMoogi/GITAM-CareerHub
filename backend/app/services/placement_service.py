"""
Internship & Placement Engine — Service Layer.

Business rules:
  1. Eligibility check:
       - student's overall readiness score >= posting's minimum_readiness_score
       - student's branch in allowed_branches (if set)
       - student's CGPA >= minimum_cgpa (if set)
  2. Duplicate prevention: one application per (student, internship/placement_job)
  3. Status pipeline: APPLIED → SHORTLISTED → ONLINE_TEST → TECHNICAL → HR → SELECTED/REJECTED
  4. Offer letter auto-generated when status = SELECTED
  5. Dashboard: real-time application summary statistics
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException, BadRequestException
from app.models.company import Company
from app.models.job_role import JobRole
from app.models.placement import (
    Internship, PlacementJob, StudentApplication, InterviewSchedule, OfferLetter,
)
from app.models.student import Student
from app.models.student_company_readiness import StudentCompanyReadiness
from app.schemas.placement import (
    ApplicationCreate, ApplicationRead, ApplicationStatusUpdate,
    ApplicationSummary, InterviewScheduleRead, InternshipDetailRead,
    InternshipListRead, OfferLetterRead, PlacementDashboard,
    PlacementJobDetailRead, PlacementJobListRead,
)

logger = logging.getLogger("app.services.placement_service")

VALID_STATUS_TRANSITIONS = {
    "SAVED":         ["APPLIED"],
    "APPLIED":       ["SHORTLISTED", "REJECTED"],
    "SHORTLISTED":   ["ONLINE_TEST", "REJECTED"],
    "ONLINE_TEST":   ["TECHNICAL", "REJECTED"],
    "TECHNICAL":     ["HR", "REJECTED"],
    "HR":            ["SELECTED", "REJECTED"],
    "SELECTED":      [],
    "REJECTED":      [],
}


class PlacementService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _get_student(self, user_id: str) -> Student:
        res = await self.db.execute(
            select(Student)
            .where(Student.user_id == user_id)
            .options(selectinload(Student.branch))
        )
        student = res.unique().scalars().first()
        if not student:
            raise NotFoundException(message="Student profile not found.")
        return student

    async def _get_readiness_score(self, student_id: str, company_id: str) -> float:
        """Return the cached overall readiness score for student↔company."""
        res = await self.db.execute(
            select(StudentCompanyReadiness).where(
                StudentCompanyReadiness.student_id == student_id,
                StudentCompanyReadiness.company_id == company_id,
                StudentCompanyReadiness.job_role_id.is_(None),
            )
        )
        rec = res.scalars().first()
        return rec.overall_score if rec else 0.0

    def _check_branch_eligibility(self, student: Student, allowed_branches: Optional[str]) -> bool:
        """Returns True if student's branch code is in allowed_branches (or it's NULL=all)."""
        if not allowed_branches:
            return True
        branch_code = student.branch.code if student.branch else ""
        allowed = [b.strip().upper() for b in allowed_branches.split(",")]
        return branch_code.upper() in allowed

    async def _build_eligibility(
        self, student: Student, company_id: str,
        min_readiness: float, allowed_branches: Optional[str], min_cgpa: Optional[float],
    ):
        """Returns (is_eligible: bool, reason: str | None)."""
        readiness = await self._get_readiness_score(student.id, company_id)
        if readiness < min_readiness:
            return False, f"Readiness score {readiness:.1f} is below required {min_readiness:.1f}"
        if not self._check_branch_eligibility(student, allowed_branches):
            return False, "Your branch is not eligible for this position"
        # CGPA check if student has CGPA attribute (optional field)
        if min_cgpa and hasattr(student, "cgpa") and student.cgpa and student.cgpa < min_cgpa:
            return False, f"CGPA {student.cgpa:.2f} is below required {min_cgpa:.2f}"
        return True, None

    def _app_to_read(self, app: StudentApplication) -> ApplicationRead:
        """Convert a StudentApplication ORM instance → ApplicationRead schema."""
        intern_title = app.internship.title if app.internship else None
        place_title  = app.placement_job.title if app.placement_job else None
        app_type     = "INTERNSHIP" if app.internship_id else "PLACEMENT"

        offer = None
        if app.offer_letter:
            ol = app.offer_letter
            offer = OfferLetterRead(
                id=ol.id,
                company_name=app.company.name if app.company else "Unknown",
                offer_type=ol.offer_type,
                package=ol.package,
                joining_date=ol.joining_date,
                offer_letter_url=ol.offer_letter_url,
                accepted=ol.accepted,
                issued_at=ol.issued_at,
            )

        schedules = [
            InterviewScheduleRead(
                id=s.id,
                round_name=s.round_name,
                scheduled_date=s.scheduled_date,
                meeting_link=s.meeting_link,
                venue=s.venue,
                status=s.status,
            )
            for s in (app.interview_schedules or [])
        ]

        return ApplicationRead(
            id=app.id,
            company_id=app.company_id,
            company_name=app.company.name if app.company else "Unknown",
            company_logo=app.company.logo if app.company else None,
            internship_id=app.internship_id,
            internship_title=intern_title,
            placement_job_id=app.placement_job_id,
            placement_job_title=place_title,
            application_type=app_type,
            status=app.status,
            application_date=app.application_date,
            last_updated=app.last_updated,
            feedback=app.feedback,
            readiness_score_at_apply=app.readiness_score_at_apply,
            interview_schedules=schedules,
            offer_letter=offer,
        )

    async def _load_application(self, application_id: str) -> Optional[StudentApplication]:
        res = await self.db.execute(
            select(StudentApplication)
            .where(StudentApplication.id == application_id)
            .options(
                selectinload(StudentApplication.company),
                selectinload(StudentApplication.internship),
                selectinload(StudentApplication.placement_job),
                selectinload(StudentApplication.interview_schedules),
                selectinload(StudentApplication.offer_letter),
            )
        )
        return res.unique().scalars().first()

    async def _generate_offer_letter(self, app: StudentApplication) -> None:
        """Auto-create an OfferLetter when a student is SELECTED."""
        existing = await self.db.execute(
            select(OfferLetter).where(OfferLetter.application_id == app.id)
        )
        if existing.scalars().first():
            return  # Already issued

        offer_type = "INTERNSHIP" if app.internship_id else "PLACEMENT"
        package = None
        joining = None

        if app.internship and app.internship.stipend:
            package = float(app.internship.stipend)
        elif app.placement_job:
            package = app.placement_job.package_min

        ol = OfferLetter(
            student_id=app.student_id,
            company_id=app.company_id,
            application_id=app.id,
            offer_type=offer_type,
            package=package,
            joining_date=joining,
        )
        self.db.add(ol)
        await self.db.flush()

    # ── Public API ────────────────────────────────────────────────────────────

    async def list_internships(
        self,
        user_id: str,
        status: str = "ACTIVE",
        mode: Optional[str] = None,
        internship_type: Optional[str] = None,
        company_id: Optional[str] = None,
    ) -> List[InternshipListRead]:
        student = await self._get_student(user_id)

        query = (
            select(Internship)
            .options(
                selectinload(Internship.company),
                selectinload(Internship.job_role),
            )
            .where(Internship.status == status)
        )
        if mode:
            query = query.where(Internship.mode == mode)
        if internship_type:
            query = query.where(Internship.internship_type == internship_type)
        if company_id:
            query = query.where(Internship.company_id == company_id)

        res = await self.db.execute(query)
        internships = res.unique().scalars().all()

        result = []
        for intern in internships:
            is_eligible, reason = await self._build_eligibility(
                student, intern.company_id,
                intern.minimum_readiness_score,
                intern.allowed_branches,
                intern.minimum_cgpa,
            )
            result.append(InternshipListRead(
                id=intern.id,
                company_id=intern.company_id,
                company_name=intern.company.name if intern.company else "Unknown",
                company_logo=intern.company.logo if intern.company else None,
                title=intern.title,
                internship_type=intern.internship_type,
                mode=intern.mode,
                stipend=intern.stipend,
                duration=intern.duration,
                location=intern.location,
                openings=intern.openings,
                application_start=intern.application_start,
                application_end=intern.application_end,
                minimum_readiness_score=intern.minimum_readiness_score,
                status=intern.status,
                is_eligible=is_eligible,
                eligibility_reason=reason,
            ))

        # Eligible first, then by readiness_score descending
        result.sort(key=lambda x: (not x.is_eligible, -x.minimum_readiness_score))
        return result

    async def get_internship_detail(self, user_id: str, internship_id: str) -> InternshipDetailRead:
        student = await self._get_student(user_id)

        res = await self.db.execute(
            select(Internship)
            .where(Internship.id == internship_id)
            .options(selectinload(Internship.company), selectinload(Internship.job_role))
        )
        intern = res.unique().scalars().first()
        if not intern:
            raise NotFoundException(message=f"Internship '{internship_id}' not found.")

        readiness = await self._get_readiness_score(student.id, intern.company_id)
        is_eligible, reason = await self._build_eligibility(
            student, intern.company_id,
            intern.minimum_readiness_score, intern.allowed_branches, intern.minimum_cgpa,
        )

        return InternshipDetailRead(
            id=intern.id,
            company_id=intern.company_id,
            company_name=intern.company.name if intern.company else "Unknown",
            company_logo=intern.company.logo if intern.company else None,
            job_role_id=intern.job_role_id,
            job_role_title=intern.job_role.title if intern.job_role else None,
            title=intern.title,
            description=intern.description,
            internship_type=intern.internship_type,
            mode=intern.mode,
            stipend=intern.stipend,
            duration=intern.duration,
            location=intern.location,
            openings=intern.openings,
            application_start=intern.application_start,
            application_end=intern.application_end,
            eligibility_criteria=intern.eligibility_criteria,
            minimum_readiness_score=intern.minimum_readiness_score,
            minimum_cgpa=intern.minimum_cgpa,
            allowed_branches=intern.allowed_branches,
            official_apply_link=intern.official_apply_link,
            status=intern.status,
            is_eligible=is_eligible,
            eligibility_reason=reason,
            student_readiness_score=readiness,
        )

    async def list_placements(
        self,
        user_id: str,
        status: str = "ACTIVE",
        company_id: Optional[str] = None,
    ) -> List[PlacementJobListRead]:
        student = await self._get_student(user_id)

        query = (
            select(PlacementJob)
            .options(
                selectinload(PlacementJob.company),
                selectinload(PlacementJob.job_role),
            )
            .where(PlacementJob.status == status)
        )
        if company_id:
            query = query.where(PlacementJob.company_id == company_id)

        res = await self.db.execute(query)
        jobs = res.unique().scalars().all()

        result = []
        for job in jobs:
            is_eligible, reason = await self._build_eligibility(
                student, job.company_id,
                job.minimum_readiness_score, job.allowed_branches, job.minimum_cgpa,
            )
            result.append(PlacementJobListRead(
                id=job.id,
                company_id=job.company_id,
                company_name=job.company.name if job.company else "Unknown",
                company_logo=job.company.logo if job.company else None,
                title=job.title,
                package_min=job.package_min,
                package_max=job.package_max,
                location=job.location,
                openings=job.openings,
                deadline=job.deadline,
                minimum_readiness_score=job.minimum_readiness_score,
                status=job.status,
                is_eligible=is_eligible,
                eligibility_reason=reason,
            ))

        result.sort(key=lambda x: (not x.is_eligible, -(x.package_max or 0)))
        return result

    async def get_placement_detail(self, user_id: str, placement_id: str) -> PlacementJobDetailRead:
        student = await self._get_student(user_id)

        res = await self.db.execute(
            select(PlacementJob)
            .where(PlacementJob.id == placement_id)
            .options(selectinload(PlacementJob.company), selectinload(PlacementJob.job_role))
        )
        job = res.unique().scalars().first()
        if not job:
            raise NotFoundException(message=f"Placement job '{placement_id}' not found.")

        readiness = await self._get_readiness_score(student.id, job.company_id)
        is_eligible, reason = await self._build_eligibility(
            student, job.company_id,
            job.minimum_readiness_score, job.allowed_branches, job.minimum_cgpa,
        )

        return PlacementJobDetailRead(
            id=job.id,
            company_id=job.company_id,
            company_name=job.company.name if job.company else "Unknown",
            company_logo=job.company.logo if job.company else None,
            job_role_id=job.job_role_id,
            job_role_title=job.job_role.title if job.job_role else None,
            title=job.title,
            description=job.description,
            package_min=job.package_min,
            package_max=job.package_max,
            location=job.location,
            openings=job.openings,
            bond=job.bond,
            deadline=job.deadline,
            eligibility_criteria=job.eligibility_criteria,
            minimum_readiness_score=job.minimum_readiness_score,
            minimum_cgpa=job.minimum_cgpa,
            allowed_branches=job.allowed_branches,
            official_apply_link=job.official_apply_link,
            status=job.status,
            is_eligible=is_eligible,
            eligibility_reason=reason,
            student_readiness_score=readiness,
        )

    async def apply(self, user_id: str, payload: ApplicationCreate) -> ApplicationRead:
        """
        Apply to an internship or placement job.
        Enforces eligibility before creating the application.
        """
        if not payload.internship_id and not payload.placement_job_id:
            raise BadRequestException(message="Provide either internship_id or placement_job_id.")
        if payload.internship_id and payload.placement_job_id:
            raise BadRequestException(message="Apply to internship OR placement job, not both at once.")

        student = await self._get_student(user_id)
        now = datetime.now(timezone.utc)

        if payload.internship_id:
            res = await self.db.execute(
                select(Internship)
                .where(Internship.id == payload.internship_id)
                .options(selectinload(Internship.company), selectinload(Internship.job_role))
            )
            posting = res.unique().scalars().first()
            if not posting:
                raise NotFoundException(message="Internship not found.")
            if posting.status != "ACTIVE":
                raise BadRequestException(message=f"This internship is currently {posting.status}.")

            is_eligible, reason = await self._build_eligibility(
                student, posting.company_id,
                posting.minimum_readiness_score, posting.allowed_branches, posting.minimum_cgpa,
            )
            if not is_eligible:
                raise BadRequestException(message=f"Not eligible: {reason}")

            # Duplicate check
            dup_res = await self.db.execute(
                select(StudentApplication).where(
                    StudentApplication.student_id == student.id,
                    StudentApplication.internship_id == payload.internship_id,
                )
            )
            if dup_res.scalars().first():
                raise BadRequestException(message="You have already applied for this internship.")

            readiness = await self._get_readiness_score(student.id, posting.company_id)
            app = StudentApplication(
                student_id=student.id,
                company_id=posting.company_id,
                internship_id=payload.internship_id,
                status="APPLIED",
                application_date=now,
                last_updated=now,
                readiness_score_at_apply=readiness,
            )

        else:  # placement_job_id
            res = await self.db.execute(
                select(PlacementJob)
                .where(PlacementJob.id == payload.placement_job_id)
                .options(selectinload(PlacementJob.company), selectinload(PlacementJob.job_role))
            )
            posting = res.unique().scalars().first()
            if not posting:
                raise NotFoundException(message="Placement job not found.")
            if posting.status != "ACTIVE":
                raise BadRequestException(message=f"This placement job is currently {posting.status}.")

            is_eligible, reason = await self._build_eligibility(
                student, posting.company_id,
                posting.minimum_readiness_score, posting.allowed_branches, posting.minimum_cgpa,
            )
            if not is_eligible:
                raise BadRequestException(message=f"Not eligible: {reason}")

            dup_res = await self.db.execute(
                select(StudentApplication).where(
                    StudentApplication.student_id == student.id,
                    StudentApplication.placement_job_id == payload.placement_job_id,
                )
            )
            if dup_res.scalars().first():
                raise BadRequestException(message="You have already applied for this placement job.")

            readiness = await self._get_readiness_score(student.id, posting.company_id)
            app = StudentApplication(
                student_id=student.id,
                company_id=posting.company_id,
                placement_job_id=payload.placement_job_id,
                status="APPLIED",
                application_date=now,
                last_updated=now,
                readiness_score_at_apply=readiness,
            )

        self.db.add(app)
        await self.db.commit()

        full_app = await self._load_application(app.id)
        return self._app_to_read(full_app)

    async def update_status(
        self, application_id: str, payload: ApplicationStatusUpdate
    ) -> ApplicationRead:
        """
        Update an application's stage. Only valid forward transitions are allowed.
        Auto-generates offer letter when SELECTED.
        """
        app = await self._load_application(application_id)
        if not app:
            raise NotFoundException(message="Application not found.")

        allowed_next = VALID_STATUS_TRANSITIONS.get(app.status, [])
        if payload.status not in allowed_next:
            raise BadRequestException(
                message=f"Cannot transition from '{app.status}' to '{payload.status}'. "
                        f"Allowed: {allowed_next}"
            )

        app.status = payload.status
        app.last_updated = datetime.now(timezone.utc)
        if payload.feedback:
            app.feedback = payload.feedback

        # Auto-generate offer letter on SELECTED
        if payload.status == "SELECTED":
            await self._generate_offer_letter(app)

        await self.db.commit()
        return self._app_to_read(await self._load_application(app.id))

    async def get_my_applications(
        self, user_id: str,
        status: Optional[str] = None,
        application_type: Optional[str] = None,
    ) -> List[ApplicationRead]:
        """Return all applications for the authenticated student."""
        student = await self._get_student(user_id)

        query = (
            select(StudentApplication)
            .where(StudentApplication.student_id == student.id)
            .options(
                selectinload(StudentApplication.company),
                selectinload(StudentApplication.internship),
                selectinload(StudentApplication.placement_job),
                selectinload(StudentApplication.interview_schedules),
                selectinload(StudentApplication.offer_letter),
            )
            .order_by(StudentApplication.last_updated.desc())
        )
        if status:
            query = query.where(StudentApplication.status == status)
        if application_type == "INTERNSHIP":
            query = query.where(StudentApplication.internship_id.isnot(None))
        elif application_type == "PLACEMENT":
            query = query.where(StudentApplication.placement_job_id.isnot(None))

        res = await self.db.execute(query)
        apps = res.unique().scalars().all()
        return [self._app_to_read(a) for a in apps]

    async def get_dashboard(self, user_id: str) -> PlacementDashboard:
        """Full dashboard: stats + recent applications + active listings."""
        student = await self._get_student(user_id)

        # All applications for summary stats
        res = await self.db.execute(
            select(StudentApplication)
            .where(StudentApplication.student_id == student.id)
            .options(
                selectinload(StudentApplication.company),
                selectinload(StudentApplication.internship),
                selectinload(StudentApplication.placement_job),
                selectinload(StudentApplication.interview_schedules),
                selectinload(StudentApplication.offer_letter),
            )
        )
        all_apps = res.unique().scalars().all()

        # Compute summary
        status_counts = {}
        for a in all_apps:
            status_counts[a.status] = status_counts.get(a.status, 0) + 1

        offers = [a for a in all_apps if a.offer_letter]
        summary = ApplicationSummary(
            total_applications=len(all_apps),
            saved=status_counts.get("SAVED", 0),
            applied=status_counts.get("APPLIED", 0),
            shortlisted=status_counts.get("SHORTLISTED", 0),
            in_progress=(
                status_counts.get("ONLINE_TEST", 0) +
                status_counts.get("TECHNICAL", 0) +
                status_counts.get("HR", 0)
            ),
            selected=status_counts.get("SELECTED", 0),
            rejected=status_counts.get("REJECTED", 0),
            offers_received=len(offers),
            offers_accepted=sum(1 for a in offers if a.offer_letter and a.offer_letter.accepted),
        )

        recent_apps = sorted(all_apps, key=lambda x: x.last_updated, reverse=True)[:5]

        # Active internships & placements with eligibility context
        active_internships = await self.list_internships(user_id, status="ACTIVE")
        active_placements  = await self.list_placements(user_id, status="ACTIVE")

        return PlacementDashboard(
            summary=summary,
            recent_applications=[self._app_to_read(a) for a in recent_apps],
            active_internships=active_internships[:10],
            active_placements=active_placements[:10],
        )

    async def get_offer_letters(self, user_id: str) -> List[OfferLetterRead]:
        """Return all offer letters for the authenticated student."""
        student = await self._get_student(user_id)
        res = await self.db.execute(
            select(OfferLetter)
            .where(OfferLetter.student_id == student.id)
            .options(selectinload(OfferLetter.company))
            .order_by(OfferLetter.issued_at.desc())
        )
        offers = res.unique().scalars().all()
        return [
            OfferLetterRead(
                id=ol.id,
                company_name=ol.company.name if ol.company else "Unknown",
                offer_type=ol.offer_type,
                package=ol.package,
                joining_date=ol.joining_date,
                offer_letter_url=ol.offer_letter_url,
                accepted=ol.accepted,
                issued_at=ol.issued_at,
            )
            for ol in offers
        ]

    async def accept_offer(self, user_id: str, offer_id: str, accept: bool) -> OfferLetterRead:
        """Accept or decline an offer letter."""
        student = await self._get_student(user_id)
        res = await self.db.execute(
            select(OfferLetter)
            .where(OfferLetter.id == offer_id, OfferLetter.student_id == student.id)
            .options(selectinload(OfferLetter.company))
        )
        ol = res.unique().scalars().first()
        if not ol:
            raise NotFoundException(message="Offer letter not found.")
        ol.accepted = accept
        await self.db.commit()
        return OfferLetterRead(
            id=ol.id,
            company_name=ol.company.name if ol.company else "Unknown",
            offer_type=ol.offer_type,
            package=ol.package,
            joining_date=ol.joining_date,
            offer_letter_url=ol.offer_letter_url,
            accepted=ol.accepted,
            issued_at=ol.issued_at,
        )
