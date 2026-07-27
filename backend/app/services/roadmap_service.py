import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.models.roadmap import Roadmap
from app.models.roadmap_dependency import RoadmapModuleDependency
from app.models.roadmap_module import RoadmapModule
from app.models.student import Student
from app.models.student_progress import StudentRoadmapProgress
from app.schemas.roadmap import (
    ProgressStatus,
    RoadmapModuleRead,
    RoadmapRead,
    StudentProgressRead,
    UpdateModuleProgressRequest,
)

logger = logging.getLogger("app.services.roadmap_service")


class RoadmapService:
    """
    Business logic layer for the Academic Roadmap Engine.
    Handles roadmap retrieval, module lock resolution, and student progress tracking.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ─── Internal Helpers ──────────────────────────────────────────────────────

    async def _get_student(self, user_id: str) -> Student:
        query = select(Student).where(Student.user_id == user_id)
        result = await self.db.execute(query)
        student = result.scalars().first()
        if not student:
            raise NotFoundException(message="Student profile not found.")
        return student

    async def _get_student_progress_map(
        self, student_id: str
    ) -> Dict[str, StudentRoadmapProgress]:
        """Return a dict of roadmap_module_id -> StudentRoadmapProgress for a student."""
        query = select(StudentRoadmapProgress).where(
            StudentRoadmapProgress.student_id == student_id
        )
        result = await self.db.execute(query)
        rows = result.unique().scalars().all()
        return {r.roadmap_module_id: r for r in rows}

    async def _get_all_dependencies(self) -> Dict[str, List[RoadmapModuleDependency]]:
        """Return dict of module_id -> list of its prerequisites (dependencies)."""
        query = select(RoadmapModuleDependency)
        result = await self.db.execute(query)
        deps = result.unique().scalars().all()
        dep_map: Dict[str, List[RoadmapModuleDependency]] = {}
        for d in deps:
            dep_map.setdefault(d.module_id, []).append(d)
        return dep_map

    def _resolve_lock_status(
        self,
        module: RoadmapModule,
        roadmap: Roadmap,
        student: Student,
        progress_map: Dict[str, StudentRoadmapProgress],
        dep_map: Dict[str, List[RoadmapModuleDependency]],
        all_modules: Dict[str, RoadmapModule],
    ) -> tuple[bool, Optional[str], List[str]]:
        """
        Compute lock status for a module relative to a student.
        Returns (is_locked, lock_reason, list_of_prerequisite_names).
        """
        prerequisites = []

        # ── Rule 1: Future semester lock ──────────────────────────────────────
        roadmap_sem_num = roadmap.semester.semester_number
        student_sem_num = student.semester

        if roadmap_sem_num > student_sem_num:
            return (
                True,
                f"Future semester locked (Semester {roadmap_sem_num} requires completion of Semester {student_sem_num})",
                prerequisites,
            )

        # ── Rule 2: Prerequisite dependency lock ─────────────────────────────
        deps = dep_map.get(module.id, [])
        for dep in deps:
            prereq_mod = all_modules.get(dep.depends_on_module_id)
            prereq_name = prereq_mod.module_name if prereq_mod else dep.depends_on_module_id
            prerequisites.append(prereq_name)

            prog = progress_map.get(dep.depends_on_module_id)
            if not prog or prog.status not in (ProgressStatus.COMPLETED, ProgressStatus.SKIPPED):
                return (
                    True,
                    f"Prerequisite not completed: '{prereq_name}'",
                    prerequisites,
                )

        return (False, None, prerequisites)

    def _build_module_read(
        self,
        module: RoadmapModule,
        roadmap: Roadmap,
        student: Student,
        progress_map: Dict[str, StudentRoadmapProgress],
        dep_map: Dict[str, List[RoadmapModuleDependency]],
        all_modules: Dict[str, RoadmapModule],
    ) -> RoadmapModuleRead:
        is_locked, lock_reason, prerequisites = self._resolve_lock_status(
            module, roadmap, student, progress_map, dep_map, all_modules
        )
        prog = progress_map.get(module.id)
        user_status = prog.status if prog else ProgressStatus.NOT_STARTED
        completion_pct = prog.completion_percentage if prog else 0.0
        started_at = prog.started_at if prog else None
        completed_at = prog.completed_at if prog else None

        return RoadmapModuleRead(
            id=module.id,
            roadmap_id=module.roadmap_id,
            module_name=module.module_name,
            module_type=module.module_type,
            display_order=module.display_order,
            is_required=module.is_required,
            estimated_hours=module.estimated_hours,
            user_status=user_status,
            completion_percentage=completion_pct,
            is_locked=is_locked,
            lock_reason=lock_reason,
            prerequisites=prerequisites,
            started_at=started_at,
            completed_at=completed_at,
        )

    # ─── Public API Methods ────────────────────────────────────────────────────

    async def get_roadmaps_for_student(
        self,
        user_id: str,
        year: Optional[int] = None,
        semester: Optional[int] = None,
    ) -> List[RoadmapRead]:
        """
        Returns all active roadmaps for the student's branch.
        Optionally filtered by year or semester.
        """
        student = await self._get_student(user_id)

        query = (
            select(Roadmap)
            .where(Roadmap.branch_id == student.branch_id, Roadmap.is_active == True)
            .order_by(Roadmap.display_order)
        )
        result = await self.db.execute(query)
        roadmaps = result.unique().scalars().all()

        # Apply optional filters
        if year is not None:
            roadmaps = [r for r in roadmaps if r.academic_year.year_number == year]
        if semester is not None:
            roadmaps = [r for r in roadmaps if r.semester.semester_number == semester]

        progress_map = await self._get_student_progress_map(student.id)
        dep_map = await self._get_all_dependencies()

        # Build flat module index for lock resolution
        all_module_ids = [m.id for r in roadmaps for m in r.modules]
        all_modules: Dict[str, RoadmapModule] = {}
        if all_module_ids:
            mod_query = select(RoadmapModule).where(RoadmapModule.id.in_(all_module_ids))
            mod_result = await self.db.execute(mod_query)
            for m in mod_result.unique().scalars().all():
                all_modules[m.id] = m

        output = []
        for roadmap in roadmaps:
            modules_read = [
                self._build_module_read(m, roadmap, student, progress_map, dep_map, all_modules)
                for m in sorted(roadmap.modules, key=lambda x: x.display_order)
            ]
            output.append(
                RoadmapRead(
                    id=roadmap.id,
                    title=roadmap.title,
                    description=roadmap.description,
                    branch_id=roadmap.branch_id,
                    branch_name=roadmap.branch.name,
                    academic_year_id=roadmap.academic_year_id,
                    year_number=roadmap.academic_year.year_number,
                    semester_id=roadmap.semester_id,
                    semester_number=roadmap.semester.semester_number,
                    display_order=roadmap.display_order,
                    is_active=roadmap.is_active,
                    modules=modules_read,
                    total_estimated_hours=sum(m.estimated_hours for m in roadmap.modules),
                )
            )
        return output

    async def get_modules_for_student(
        self,
        user_id: str,
        semester: Optional[int] = None,
    ) -> List[RoadmapModuleRead]:
        """
        Returns ALL ordered modules across all roadmaps for the student's branch,
        enriched with lock status and progress state.
        Optionally filtered to a specific semester.
        """
        student = await self._get_student(user_id)

        roadmap_query = (
            select(Roadmap)
            .where(Roadmap.branch_id == student.branch_id, Roadmap.is_active == True)
            .order_by(Roadmap.display_order)
        )
        result = await self.db.execute(roadmap_query)
        roadmaps = result.unique().scalars().all()

        if semester is not None:
            roadmaps = [r for r in roadmaps if r.semester.semester_number == semester]

        progress_map = await self._get_student_progress_map(student.id)
        dep_map = await self._get_all_dependencies()

        # Build a flat global module index for cross-roadmap dep resolution
        all_roadmap_ids = [r.id for r in roadmaps]
        all_modules: Dict[str, RoadmapModule] = {}
        if all_roadmap_ids:
            mod_query = select(RoadmapModule).where(RoadmapModule.roadmap_id.in_(all_roadmap_ids))
            mod_result = await self.db.execute(mod_query)
            for m in mod_result.unique().scalars().all():
                all_modules[m.id] = m

        # Also load all module ids from other roadmaps so cross-deps can resolve
        all_mods_query = select(RoadmapModule)
        all_mods_result = await self.db.execute(all_mods_query)
        for m in all_mods_result.unique().scalars().all():
            all_modules.setdefault(m.id, m)

        output = []
        for roadmap in roadmaps:
            for module in sorted(roadmap.modules, key=lambda x: x.display_order):
                output.append(
                    self._build_module_read(
                        module, roadmap, student, progress_map, dep_map, all_modules
                    )
                )
        return output

    async def get_student_progress(self, user_id: str) -> StudentProgressRead:
        """
        Computes aggregate progress metrics for a student.
        Returns completed %, counts, and categorized module lists.
        """
        student = await self._get_student(user_id)

        roadmap_query = (
            select(Roadmap)
            .where(Roadmap.branch_id == student.branch_id, Roadmap.is_active == True)
            .order_by(Roadmap.display_order)
        )
        result = await self.db.execute(roadmap_query)
        roadmaps = result.unique().scalars().all()

        progress_map = await self._get_student_progress_map(student.id)
        dep_map = await self._get_all_dependencies()

        all_modules: Dict[str, RoadmapModule] = {}
        all_mods_query = select(RoadmapModule)
        all_mods_result = await self.db.execute(all_mods_query)
        for m in all_mods_result.unique().scalars().all():
            all_modules[m.id] = m

        completed: List[RoadmapModuleRead] = []
        in_progress: List[RoadmapModuleRead] = []
        locked: List[RoadmapModuleRead] = []
        upcoming: List[RoadmapModuleRead] = []

        total_hours = 0
        completed_hours = 0

        for roadmap in roadmaps:
            for module in sorted(roadmap.modules, key=lambda x: x.display_order):
                m_read = self._build_module_read(
                    module, roadmap, student, progress_map, dep_map, all_modules
                )
                total_hours += module.estimated_hours

                if m_read.user_status == ProgressStatus.COMPLETED:
                    completed.append(m_read)
                    completed_hours += module.estimated_hours
                elif m_read.user_status == ProgressStatus.IN_PROGRESS:
                    in_progress.append(m_read)
                elif m_read.is_locked:
                    locked.append(m_read)
                else:
                    upcoming.append(m_read)

        total_modules = len(completed) + len(in_progress) + len(locked) + len(upcoming)
        overall_pct = round(len(completed) / total_modules * 100, 2) if total_modules > 0 else 0.0

        return StudentProgressRead(
            overall_completion_percentage=overall_pct,
            completed_modules_count=len(completed),
            in_progress_modules_count=len(in_progress),
            total_modules_count=total_modules,
            total_estimated_hours=total_hours,
            completed_estimated_hours=completed_hours,
            completed_modules=completed,
            in_progress_modules=in_progress,
            locked_modules=locked,
            upcoming_modules=upcoming,
        )

    async def update_module_progress(
        self,
        user_id: str,
        module_id: str,
        payload: UpdateModuleProgressRequest,
        is_admin: bool = False,
    ) -> RoadmapModuleRead:
        """
        Update a student's progress status on a specific module.
        SKIPPED status requires admin privileges.
        """
        # Validate allowed status values
        allowed = [ProgressStatus.IN_PROGRESS, ProgressStatus.COMPLETED, ProgressStatus.SKIPPED]
        if payload.status not in allowed:
            raise BadRequestException(
                message=f"Invalid status '{payload.status}'. Allowed: {', '.join(allowed)}"
            )

        if payload.status == ProgressStatus.SKIPPED and not is_admin:
            raise ForbiddenException(
                message="Only administrators can mark modules as SKIPPED."
            )

        student = await self._get_student(user_id)
        progress_map = await self._get_student_progress_map(student.id)
        dep_map = await self._get_all_dependencies()

        # Fetch the module
        module = await self.db.get(RoadmapModule, module_id)
        if not module:
            raise NotFoundException(message=f"Roadmap module '{module_id}' not found.")

        # Fetch the roadmap for this module
        roadmap = await self.db.get(Roadmap, module.roadmap_id)
        if not roadmap:
            raise NotFoundException(message="Roadmap not found for this module.")

        # Build full module index for lock resolution
        all_mods_result = await self.db.execute(select(RoadmapModule))
        all_modules = {m.id: m for m in all_mods_result.unique().scalars().all()}

        # Check if module is locked (only block if not admin)
        if not is_admin:
            is_locked, lock_reason, _ = self._resolve_lock_status(
                module, roadmap, student, progress_map, dep_map, all_modules
            )
            if is_locked:
                raise BadRequestException(
                    message=f"Cannot update progress — module is locked: {lock_reason}"
                )

        now = datetime.now(timezone.utc)

        # Upsert StudentRoadmapProgress
        existing = progress_map.get(module_id)
        if not existing:
            existing = StudentRoadmapProgress(
                student_id=student.id,
                roadmap_module_id=module_id,
                status=payload.status,
                completion_percentage=0.0,
            )
            self.db.add(existing)

        existing.status = payload.status

        if payload.completion_percentage is not None:
            existing.completion_percentage = payload.completion_percentage
        elif payload.status == ProgressStatus.COMPLETED:
            existing.completion_percentage = 100.0
        elif payload.status == ProgressStatus.IN_PROGRESS and existing.completion_percentage == 0.0:
            existing.completion_percentage = 10.0

        if payload.status == ProgressStatus.IN_PROGRESS and not existing.started_at:
            existing.started_at = now
        if payload.status == ProgressStatus.COMPLETED:
            existing.completed_at = now
            if not existing.started_at:
                existing.started_at = now

        await self.db.commit()
        await self.db.refresh(existing)

        # Rebuild progress_map and return fresh module read
        progress_map[module_id] = existing
        return self._build_module_read(
            module, roadmap, student, progress_map, dep_map, all_modules
        )
