import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.database.base import Base
from app.database.session import AsyncSessionLocal
from app.database.seed_projects import DEFAULT_PROJECT_TECHNOLOGIES, PROJECT_SEED
from app.database.seed_certifications import CERTIFICATION_SEED
from app.database.seed_companies import COMPANY_SEED
from app.models.branch import Branch
from app.models.target_role import TargetRole
from app.models.academic_year import AcademicYear
from app.models.semester import Semester
from app.models.roadmap import Roadmap
from app.models.roadmap_module import RoadmapModule
from app.models.roadmap_dependency import RoadmapModuleDependency
from app.models.skill import Skill
from app.models.course import Course
from app.models.course_resource import CourseResource
from app.models.course_outcome import CourseOutcome
from app.models.course_skill import CourseSkill
from app.models.project_technology import ProjectTechnology
from app.models.project import Project
from app.models.project_skill import ProjectSkill, ProjectTechnologyMap
from app.models.project_content import (
    ProjectResource, ProjectDeliverable,
    ProjectInterviewQuestion, ProjectResumePoint,
)
from app.models.certification import Certification
from app.models.certification_skill import CertificationSkill, CertificationPrerequisite
from app.models.certification_content import CertificationExam, CertificationBenefit
from app.models.company import Company
from app.models.job_role import JobRole
from app.models.company_mapping import CompanySkill, CompanyCourse, CompanyProject, CompanyCertification
from app.models.company_interview import CompanyInterviewRound, CompanyInterviewQuestion
from app.models.placement import Internship, PlacementJob
from app.models.gamification import Level, Achievement, Badge, DailyChallenge, WeeklyChallenge, MonthlyChallenge, Reward
from app.database.seed_placement import INTERNSHIP_SEED, PLACEMENT_SEED
from app.database.seed_gamification import (
    LEVELS_SEED, ACHIEVEMENTS_SEED, BADGES_SEED,
    DAILY_CHALLENGES_SEED, WEEKLY_CHALLENGES_SEED, MONTHLY_CHALLENGES_SEED, REWARDS_SEED
)
import app.models  # noqa: F401

logger = logging.getLogger("app.database.init_db")

DEFAULT_BRANCHES = [
    {"code": "AIML", "name": "Artificial Intelligence & Machine Learning", "description": "AI & ML Specialization"},
    {"code": "ECE", "name": "Electronics & Communication Engineering", "description": "Electronics & Communication"},
    {"code": "EEE", "name": "Electrical & Electronics Engineering", "description": "Electrical Systems & Power"},
    {"code": "Mechanical", "name": "Mechanical Engineering", "description": "Mechanical & Design Engineering"},
]

DEFAULT_TARGET_ROLES = [
    {"title": "Embedded Engineer", "description": "Embedded Systems and Microcontrollers"},
    {"title": "VLSI Engineer", "description": "Very Large Scale Integration and Chip Design"},
    {"title": "AI Engineer", "description": "Artificial Intelligence and Machine Learning"},
    {"title": "Data Scientist", "description": "Data Analytics and Predictive Modeling"},
    {"title": "Automation Engineer", "description": "Industrial & Software Test Automation"},
    {"title": "Design Engineer", "description": "CAD, Mechanical & Product Design"},
    {"title": "Mechanical Design Engineer", "description": "Mechanical Component & Structural Design"},
    {"title": "Power Systems Engineer", "description": "Electrical Power Systems & Smart Grids"},
]

DEFAULT_SKILLS = [
    {"name": "Python", "category": "Programming", "description": "General-purpose programming language"},
    {"name": "C Programming", "category": "Programming", "description": "System-level programming language"},
    {"name": "Embedded C", "category": "Programming", "description": "C for microcontrollers and embedded systems"},
    {"name": "Digital Electronics", "category": "Electronics", "description": "Digital circuits and logic design"},
    {"name": "PCB Design", "category": "Electronics", "description": "Printed Circuit Board design"},
    {"name": "STM32", "category": "Embedded Systems", "description": "ARM Cortex-M based STM32 programming"},
    {"name": "Arduino", "category": "Embedded Systems", "description": "Open-source microcontroller platform"},
    {"name": "Signal Processing", "category": "Communication", "description": "Digital and analog signal analysis"},
    {"name": "MATLAB", "category": "Simulation", "description": "Mathematical computing environment"},
    {"name": "PLC Programming", "category": "Automation", "description": "Programmable Logic Controller programming"},
    {"name": "Power Systems", "category": "Electrical", "description": "Electrical power transmission systems"},
    {"name": "SCADA", "category": "Automation", "description": "Supervisory Control and Data Acquisition"},
    {"name": "Machine Learning", "category": "AI/ML", "description": "Supervised and unsupervised learning"},
    {"name": "TensorFlow", "category": "AI/ML", "description": "Deep learning framework by Google"},
    {"name": "Computer Vision", "category": "AI/ML", "description": "Image recognition and scene understanding"},
    {"name": "Data Structures", "category": "Computer Science", "description": "Arrays, linked lists, trees, graphs"},
    {"name": "AutoCAD", "category": "CAD/Design", "description": "2D and 3D CAD drafting tool"},
    {"name": "SolidWorks", "category": "CAD/Design", "description": "3D CAD modeling software"},
    {"name": "Finite Element Analysis", "category": "Simulation", "description": "Structural and thermal FEA"},
    {"name": "Thermodynamics", "category": "Mechanical", "description": "Heat transfer and energy systems"},
    {"name": "CNC Machining", "category": "Manufacturing", "description": "CNC programming and manufacturing"},
    {"name": "ROS (Robot Operating System)", "category": "Robotics", "description": "Robot software framework"},
]

COURSE_SEED = {
    "AIML": [
        {
            "title": "Python for AI & Data Science", "description": "Comprehensive Python for data science.",
            "difficulty": "BEGINNER", "estimated_hours": 30, "semester_num": 1,
            "learning_objectives": "Master Python syntax\nWork with NumPy arrays",
            "prerequisites": "Basic computer knowledge",
            "skills": [("Python", "INTERMEDIATE"), ("Data Structures", "BEGINNER")],
            "resources": [{"type": "YOUTUBE", "title": "Python Full Course", "url": "https://youtube.com/watch?v=rfscVS0vtbw", "provider": "freeCodeCamp", "order": 1, "duration": "4 hours"}],
            "outcomes": [{"title": "Write Python scripts for data manipulation", "order": 1}],
        },
        {
            "title": "Machine Learning Fundamentals", "description": "Core ML algorithms.",
            "difficulty": "INTERMEDIATE", "estimated_hours": 45, "semester_num": 3,
            "learning_objectives": "Implement supervised learning\nEvaluate model performance",
            "prerequisites": "Python",
            "skills": [("Machine Learning", "INTERMEDIATE"), ("Python", "ADVANCED")],
            "resources": [{"type": "NPTEL", "title": "ML Course - NPTEL", "url": "https://nptel.ac.in/courses/106/106/106106139/", "provider": "NPTEL IIT", "order": 1, "duration": "11 weeks"}],
            "outcomes": [{"title": "Build and train supervised ML models", "order": 1}],
        },
        {
            "title": "Deep Learning with TensorFlow", "description": "Neural networks and CNNs.",
            "difficulty": "ADVANCED", "estimated_hours": 50, "semester_num": 4,
            "learning_objectives": "Build deep neural networks\nTrain CNNs",
            "prerequisites": "Machine Learning",
            "skills": [("TensorFlow", "ADVANCED"), ("Machine Learning", "ADVANCED")],
            "resources": [{"type": "OFFICIAL_DOCS", "title": "TensorFlow Tutorials", "url": "https://www.tensorflow.org/tutorials", "provider": "Google", "order": 1, "duration": "Self-paced"}],
            "outcomes": [{"title": "Design and train deep neural networks", "order": 1}],
        },
        {
            "title": "Computer Vision with OpenCV", "description": "Image processing and detection.",
            "difficulty": "ADVANCED", "estimated_hours": 40, "semester_num": 5,
            "learning_objectives": "Process images using OpenCV\nImplement object detection",
            "prerequisites": "Deep Learning",
            "skills": [("Computer Vision", "ADVANCED"), ("Python", "ADVANCED")],
            "resources": [{"type": "OFFICIAL_DOCS", "title": "OpenCV Docs", "url": "https://docs.opencv.org/", "provider": "OpenCV", "order": 1, "duration": "Self-paced"}],
            "outcomes": [{"title": "Process images using OpenCV", "order": 1}],
        },
    ],
    "ECE": [
        {
            "title": "C Programming for Engineers", "description": "Procedural C programming for ECE.",
            "difficulty": "BEGINNER", "estimated_hours": 25, "semester_num": 1,
            "learning_objectives": "Write C programs with pointers",
            "prerequisites": "None",
            "skills": [("C Programming", "INTERMEDIATE"), ("Data Structures", "BEGINNER")],
            "resources": [{"type": "NPTEL", "title": "Programming in C - NPTEL", "url": "https://nptel.ac.in/courses/106/105/106105171/", "provider": "NPTEL IIT Bombay", "order": 1, "duration": "8 weeks"}],
            "outcomes": [{"title": "Write modular C programs", "order": 1}],
        },
        {
            "title": "Embedded Systems with Arduino", "description": "Microcontroller fundamentals.",
            "difficulty": "INTERMEDIATE", "estimated_hours": 35, "semester_num": 2,
            "learning_objectives": "Interface sensors and actuators",
            "prerequisites": "C Programming",
            "skills": [("Arduino", "INTERMEDIATE"), ("Embedded C", "BEGINNER")],
            "resources": [{"type": "OFFICIAL_DOCS", "title": "Arduino Reference", "url": "https://www.arduino.cc/reference/en/", "provider": "Arduino", "order": 1, "duration": "Self-paced"}],
            "outcomes": [{"title": "Interface sensors using I2C and SPI", "order": 1}],
        },
        {
            "title": "STM32 Microcontroller Programming", "description": "ARM Cortex-M programming.",
            "difficulty": "ADVANCED", "estimated_hours": 45, "semester_num": 4,
            "learning_objectives": "Configure STM32 peripherals",
            "prerequisites": "Arduino, C Programming",
            "skills": [("STM32", "ADVANCED"), ("Embedded C", "ADVANCED")],
            "resources": [{"type": "YOUTUBE", "title": "STM32 Tutorial", "url": "https://youtube.com/watch?v=hyZS2p1tW-g", "provider": "Phil's Lab", "order": 1, "duration": "5 hours"}],
            "outcomes": [{"title": "Configure STM32 UART, SPI, and I2C", "order": 1}],
        },
    ],
    "EEE": [
        {
            "title": "Power Electronics & Converters", "description": "DC-DC converters and inverters.",
            "difficulty": "INTERMEDIATE", "estimated_hours": 40, "semester_num": 3,
            "learning_objectives": "Design buck and boost converters",
            "prerequisites": "Circuit Analysis",
            "skills": [("Power Systems", "INTERMEDIATE"), ("MATLAB", "INTERMEDIATE")],
            "resources": [{"type": "NPTEL", "title": "Power Electronics - NPTEL", "url": "https://nptel.ac.in/courses/108/102/108102145/", "provider": "NPTEL", "order": 1, "duration": "12 weeks"}],
            "outcomes": [{"title": "Design and simulate a buck converter", "order": 1}],
        },
        {
            "title": "PLC Programming & Industrial Automation", "description": "Ladder logic and SCADA.",
            "difficulty": "INTERMEDIATE", "estimated_hours": 35, "semester_num": 4,
            "learning_objectives": "Write PLC ladder logic programs",
            "prerequisites": "Digital Electronics",
            "skills": [("PLC Programming", "ADVANCED"), ("SCADA", "INTERMEDIATE")],
            "resources": [{"type": "YOUTUBE", "title": "PLC Programming Tutorial", "url": "https://youtube.com/watch?v=_Jd0pxc7NcI", "provider": "RealPars", "order": 1, "duration": "3 hours"}],
            "outcomes": [{"title": "Write sequential PLC programs", "order": 1}],
        },
    ],
    "Mechanical": [
        {
            "title": "3D Modelling with SolidWorks", "description": "Parametric 3D modelling.",
            "difficulty": "INTERMEDIATE", "estimated_hours": 35, "semester_num": 2,
            "learning_objectives": "Create parametric 3D models",
            "prerequisites": "Engineering Drawing",
            "skills": [("SolidWorks", "INTERMEDIATE"), ("Finite Element Analysis", "BEGINNER")],
            "resources": [{"type": "YOUTUBE", "title": "SolidWorks Tutorial", "url": "https://youtube.com/watch?v=b_TtWMoKMik", "provider": "MySolidWorks", "order": 1, "duration": "5 hours"}],
            "outcomes": [{"title": "Create parametric 3D models", "order": 1}],
        },
        {
            "title": "Finite Element Analysis with ANSYS", "description": "Structural FEA.",
            "difficulty": "ADVANCED", "estimated_hours": 40, "semester_num": 4,
            "learning_objectives": "Build FEA models in ANSYS",
            "prerequisites": "3D Modelling",
            "skills": [("Finite Element Analysis", "ADVANCED"), ("SolidWorks", "INTERMEDIATE")],
            "resources": [{"type": "YOUTUBE", "title": "ANSYS Tutorial", "url": "https://youtube.com/watch?v=YyR3gy1bQ8E", "provider": "Skill-Lync", "order": 1, "duration": "3 hours"}],
            "outcomes": [{"title": "Perform static structural analysis", "order": 1}],
        },
    ],
}


async def seed_master_data(session: AsyncSession) -> None:
    """Seed all master data: branches, roles, years, semesters, roadmaps, skills, courses, technologies, projects, certifications."""

    # 1. Branches
    branch_map = {}
    for b in DEFAULT_BRANCHES:
        res = await session.execute(select(Branch).where(Branch.code == b["code"]))
        obj = res.scalars().first()
        if not obj:
            obj = Branch(code=b["code"], name=b["name"], description=b["description"])
            session.add(obj)
            await session.flush()
        branch_map[b["code"]] = obj

    # 2. Target Roles
    for r in DEFAULT_TARGET_ROLES:
        res = await session.execute(select(TargetRole).where(TargetRole.title == r["title"]))
        if not res.scalars().first():
            session.add(TargetRole(title=r["title"], description=r["description"]))

    # 3. Academic Years
    year_map = {}
    for yr_num in range(1, 5):
        res = await session.execute(select(AcademicYear).where(AcademicYear.year_number == yr_num))
        obj = res.scalars().first()
        if not obj:
            obj = AcademicYear(year_number=yr_num, name=f"Year {yr_num}")
            session.add(obj)
            await session.flush()
        year_map[yr_num] = obj

    # 4. Semesters
    sem_map = {}
    for sem_num in range(1, 9):
        res = await session.execute(select(Semester).where(Semester.semester_number == sem_num))
        obj = res.scalars().first()
        if not obj:
            yr_num = (sem_num + 1) // 2
            obj = Semester(semester_number=sem_num, name=f"Semester {sem_num}", academic_year_id=year_map[yr_num].id)
            session.add(obj)
            await session.flush()
        sem_map[sem_num] = obj
    await session.commit()

    # 5. Roadmaps & Modules
    for b_code, branch in branch_map.items():
        for sem_num, semester in sem_map.items():
            yr_num = (sem_num + 1) // 2
            parent_year = year_map[yr_num]
            res = await session.execute(select(Roadmap).where(Roadmap.branch_id == branch.id, Roadmap.semester_id == semester.id))
            if not res.scalars().first():
                roadmap = Roadmap(
                    branch_id=branch.id, academic_year_id=parent_year.id, semester_id=semester.id,
                    title=f"{b_code} - Year {yr_num} Semester {sem_num} Roadmap",
                    description=f"Core curriculum for {b_code} Semester {sem_num}.",
                    display_order=sem_num, is_active=True,
                )
                session.add(roadmap)
                await session.flush()
                modules_to_add = []
                if sem_num == 1:
                    modules_to_add.append({"name": "Student Profile & Career Goals Setup", "type": "PROFILE_SETUP", "order": 1, "hours": 2})
                modules_to_add.append({"name": f"AI Mentor Guided Learning - Semester {sem_num}", "type": "AI_LEARNING", "order": 2 if sem_num == 1 else 1, "hours": 15})
                modules_to_add.append({"name": f"{b_code} Core Fundamentals & Theory S{sem_num}", "type": "COURSE", "order": 3, "hours": 40})
                modules_to_add.append({"name": f"{b_code} Practical Technical Skills S{sem_num}", "type": "SKILL", "order": 4, "hours": 20})
                modules_to_add.append({"name": f"{b_code} Semester {sem_num} Knowledge Assessment", "type": "QUIZ", "order": 5, "hours": 5})
                modules_to_add.append({"name": f"{b_code} Capstone Practical Project S{sem_num}", "type": "PROJECT", "order": 6, "hours": 30, "depends_on_course": True})
                modules_to_add.append({"name": f"{b_code} Industry Certification Assessment S{sem_num}", "type": "CERTIFICATION", "order": 7, "hours": 15, "depends_on_project": True})
                if sem_num in [5, 6, 7]:
                    modules_to_add.append({"name": f"{b_code} Industry Internship Program S{sem_num}", "type": "INTERNSHIP", "order": 8, "hours": 80, "depends_on_project": True})
                if sem_num in [7, 8]:
                    modules_to_add.append({"name": f"{b_code} Placement Readiness & Campus Drive S{sem_num}", "type": "PLACEMENT", "order": 9, "hours": 50})
                created_modules = {}
                for m_info in modules_to_add:
                    mod = RoadmapModule(
                        roadmap_id=roadmap.id, module_name=m_info["name"],
                        module_type=m_info["type"], display_order=m_info["order"],
                        is_required=True, estimated_hours=m_info["hours"],
                    )
                    session.add(mod)
                    await session.flush()
                    created_modules[m_info["type"]] = mod
                if "PROJECT" in created_modules and "COURSE" in created_modules:
                    session.add(RoadmapModuleDependency(module_id=created_modules["PROJECT"].id, depends_on_module_id=created_modules["COURSE"].id))
                if "CERTIFICATION" in created_modules and "PROJECT" in created_modules:
                    session.add(RoadmapModuleDependency(module_id=created_modules["CERTIFICATION"].id, depends_on_module_id=created_modules["PROJECT"].id))
                if "INTERNSHIP" in created_modules and "PROJECT" in created_modules:
                    session.add(RoadmapModuleDependency(module_id=created_modules["INTERNSHIP"].id, depends_on_module_id=created_modules["PROJECT"].id))
    await session.commit()

    # 6. Skills
    skill_map = {}
    for s in DEFAULT_SKILLS:
        res = await session.execute(select(Skill).where(Skill.name == s["name"]))
        obj = res.scalars().first()
        if not obj:
            obj = Skill(name=s["name"], category=s["category"], description=s["description"])
            session.add(obj)
            await session.flush()
        skill_map[s["name"]] = obj
    await session.commit()

    # 7. Courses
    course_map = {}
    for b_code, courses in COURSE_SEED.items():
        branch = branch_map.get(b_code)
        if not branch:
            continue
        for c_data in courses:
            res = await session.execute(select(Course).where(Course.title == c_data["title"], Course.branch_id == branch.id))
            course = res.scalars().first()
            if not course:
                sem_num = c_data["semester_num"]
                yr_num = (sem_num + 1) // 2
                course = Course(
                    title=c_data["title"], description=c_data["description"],
                    branch_id=branch.id, academic_year_id=year_map[yr_num].id, semester_id=sem_map[sem_num].id,
                    difficulty=c_data["difficulty"], estimated_hours=c_data["estimated_hours"],
                    learning_objectives=c_data["learning_objectives"], prerequisites=c_data["prerequisites"],
                    status="PUBLISHED",
                )
                session.add(course)
                await session.flush()
                for r_data in c_data.get("resources", []):
                    session.add(CourseResource(
                        course_id=course.id, resource_type=r_data["type"], title=r_data["title"],
                        url=r_data["url"], provider=r_data["provider"], display_order=r_data["order"],
                        duration=r_data.get("duration"),
                    ))
                for o_data in c_data.get("outcomes", []):
                    session.add(CourseOutcome(course_id=course.id, title=o_data["title"], display_order=o_data["order"]))
                for skill_name, proficiency in c_data.get("skills", []):
                    skill = skill_map.get(skill_name)
                    if skill:
                        session.add(CourseSkill(course_id=course.id, skill_id=skill.id, proficiency_level=proficiency))
            course_map[c_data["title"]] = course
    await session.commit()

    # 8. Project Technologies
    tech_map = {}
    for t in DEFAULT_PROJECT_TECHNOLOGIES:
        res = await session.execute(select(ProjectTechnology).where(ProjectTechnology.name == t["name"]))
        obj = res.scalars().first()
        if not obj:
            obj = ProjectTechnology(name=t["name"], category=t["category"], description=t["description"])
            session.add(obj)
            await session.flush()
        tech_map[t["name"]] = obj
    await session.commit()

    # 9. Projects
    project_map = {}
    for b_code, projects in PROJECT_SEED.items():
        branch = branch_map.get(b_code)
        if not branch:
            continue
        for p_data in projects:
            res = await session.execute(select(Project).where(Project.slug == p_data["slug"]))
            project = res.scalars().first()
            if not project:
                sem_num = p_data["semester_num"]
                yr_num = (sem_num + 1) // 2
                project = Project(
                    title=p_data["title"], slug=p_data["slug"],
                    description=p_data.get("description"), problem_statement=p_data.get("problem_statement"),
                    real_world_impact=p_data.get("real_world_impact"),
                    branch_id=branch.id, academic_year_id=year_map[yr_num].id, semester_id=sem_map[sem_num].id,
                    difficulty=p_data["difficulty"], estimated_duration=p_data.get("estimated_duration"),
                    project_type=p_data["project_type"], status="PUBLISHED",
                )
                session.add(project)
                await session.flush()
                for skill_name, req_level in p_data.get("skills", []):
                    skill = skill_map.get(skill_name)
                    if skill:
                        session.add(ProjectSkill(project_id=project.id, skill_id=skill.id, required_level=req_level))
                for tech_name in p_data.get("techs", []):
                    tech = tech_map.get(tech_name)
                    if tech:
                        session.add(ProjectTechnologyMap(project_id=project.id, technology_id=tech.id))
                for r_data in p_data.get("resources", []):
                    session.add(ProjectResource(
                        project_id=project.id, resource_type=r_data["type"],
                        title=r_data["title"], url=r_data["url"], display_order=r_data["order"],
                    ))
                for d_data in p_data.get("deliverables", []):
                    session.add(ProjectDeliverable(
                        project_id=project.id, title=d_data["title"],
                        description=d_data.get("desc"), display_order=d_data["order"],
                    ))
                for q_data in p_data.get("interview_qs", []):
                    session.add(ProjectInterviewQuestion(
                        project_id=project.id, question=q_data["q"],
                        difficulty=q_data["diff"], expected_answer=q_data.get("ans"),
                    ))
                for rp_data in p_data.get("resume_points", []):
                    session.add(ProjectResumePoint(
                        project_id=project.id, resume_point=rp_data["point"],
                        display_order=rp_data["order"],
                    ))
            project_map[p_data["title"]] = project
        await session.commit()

    # 10. Certifications
    for b_code, certs in CERTIFICATION_SEED.items():
        branch = branch_map.get(b_code)
        if not branch:
            continue
        for cert_data in certs:
            res = await session.execute(
                select(Certification).where(Certification.title == cert_data["title"], Certification.branch_id == branch.id)
            )
            if res.scalars().first():
                continue
            sem_num = cert_data["semester_num"]
            yr_num = (sem_num + 1) // 2

            # Find linked CERTIFICATION RoadmapModule
            rm_res = await session.execute(
                select(RoadmapModule)
                .join(Roadmap)
                .where(
                    Roadmap.branch_id == branch.id,
                    Roadmap.semester_id == sem_map[sem_num].id,
                    RoadmapModule.module_type == "CERTIFICATION",
                )
            )
            linked_rm = rm_res.scalars().first()

            cert = Certification(
                title=cert_data["title"],
                provider=cert_data["provider"],
                provider_type=cert_data["provider_type"],
                description=cert_data.get("description"),
                official_url=cert_data.get("official_url"),
                difficulty=cert_data["difficulty"],
                estimated_hours=cert_data.get("estimated_hours"),
                branch_id=branch.id,
                academic_year_id=year_map[yr_num].id,
                semester_id=sem_map[sem_num].id,
                certificate_type="INDUSTRY" if cert_data["provider_type"] in ["AWS", "Microsoft", "Google", "Cisco", "NVIDIA"] else "ACADEMIC",
                roadmap_module_id=linked_rm.id if linked_rm else None,
                status="PUBLISHED",
            )
            session.add(cert)
            await session.flush()

            # Skills
            for skill_name, req_level in cert_data.get("skills", []):
                skill = skill_map.get(skill_name)
                if skill:
                    session.add(CertificationSkill(certification_id=cert.id, skill_id=skill.id, required_level=req_level))

            # Prerequisites
            for prereq in cert_data.get("prereqs", []):
                req_course = course_map.get(prereq.get("course_title")) if prereq.get("course_title") else None
                req_proj = project_map.get(prereq.get("project_title")) if prereq.get("project_title") else None
                session.add(CertificationPrerequisite(
                    certification_id=cert.id,
                    required_course_id=req_course.id if req_course else None,
                    required_project_id=req_proj.id if req_proj else None,
                    minimum_skill_score=prereq.get("min_score", 50.0),
                ))

            # Exams
            for exam in cert_data.get("exams", []):
                session.add(CertificationExam(
                    certification_id=cert.id,
                    exam_name=exam["name"],
                    exam_duration=exam.get("duration"),
                    passing_score=exam.get("score"),
                    exam_pattern=exam.get("pattern"),
                    official_link=exam.get("link"),
                ))

            # Benefits
            for ben in cert_data.get("benefits", []):
                session.add(CertificationBenefit(
                    certification_id=cert.id,
                    benefit=ben["benefit"],
                    display_order=ben["order"],
                ))
    await session.commit()

    # 11. Companies (Industry Intelligence Engine)
    for c_data in COMPANY_SEED:
        res = await session.execute(select(Company).where(Company.name == c_data["name"]))
        company = res.scalars().first()
        if not company:
            company = Company(
                name=c_data["name"],
                industry=c_data["industry"],
                headquarters=c_data.get("headquarters"),
                description=c_data.get("description"),
                company_size=c_data.get("company_size"),
                website=c_data.get("website"),
                careers_url=c_data.get("careers_url"),
                linkedin_url=c_data.get("linkedin_url"),
                is_hiring=c_data.get("is_hiring", True),
            )
            session.add(company)
            await session.flush()

            # Job roles
            jr_map = {}  # title -> JobRole
            for jr_data in c_data.get("job_roles", []):
                jr = JobRole(
                    company_id=company.id,
                    title=jr_data["title"],
                    role_category=jr_data["category"],
                    employment_type=jr_data["type"],
                    experience_level=jr_data["level"],
                    salary_min=jr_data.get("sal_min"),
                    salary_max=jr_data.get("sal_max"),
                    location=jr_data.get("location"),
                    status="ACTIVE",
                )
                session.add(jr)
                await session.flush()
                jr_map[jr_data["title"]] = jr

            # Required skills
            for skill_name, req_level, weightage in c_data.get("skills", []):
                skill = skill_map.get(skill_name)
                if skill:
                    session.add(CompanySkill(
                        company_id=company.id,
                        skill_id=skill.id,
                        required_level=req_level,
                        weightage=weightage,
                    ))

            # Recommended courses
            for course_title in c_data.get("rec_courses", []):
                course = course_map.get(course_title)
                if course:
                    session.add(CompanyCourse(
                        company_id=company.id,
                        course_id=course.id,
                        importance="HIGH",
                    ))

            # Recommended projects (by title lookup in project_map)
            for proj_title in c_data.get("rec_projects", []):
                proj = project_map.get(proj_title)
                if proj:
                    session.add(CompanyProject(
                        company_id=company.id,
                        project_id=proj.id,
                        importance="HIGH",
                    ))

            # Interview rounds
            for rd_data in c_data.get("interview_rounds", []):
                session.add(CompanyInterviewRound(
                    company_id=company.id,
                    round_name=rd_data["name"],
                    round_order=rd_data["order"],
                    description=rd_data.get("desc"),
                ))

            # Interview questions
            for iq_data in c_data.get("interview_qs", []):
                session.add(CompanyInterviewQuestion(
                    company_id=company.id,
                    question=iq_data["q"],
                    difficulty=iq_data["diff"],
                    category=iq_data["cat"],
                    expected_answer=iq_data.get("ans"),
                ))

        await session.commit()

    logger.info("All master seed data (branches, skills, courses, technologies, projects, certifications, companies) completed successfully.")

    # 12. Internships & Placement Jobs
    # Build a company name → Company mapping for FK lookups
    c_res = await session.execute(select(Company))
    all_companies = {c.name: c for c in c_res.unique().scalars().all()}

    for d in INTERNSHIP_SEED:
        company = all_companies.get(d["company"])
        if not company:
            logger.warning(f"Internship seed skipped: company '{d['company']}' not found")
            continue
        existing = await session.execute(
            select(Internship).where(
                Internship.company_id == company.id,
                Internship.title == d["title"],
            )
        )
        if not existing.scalars().first():
            session.add(Internship(
                company_id=company.id,
                title=d["title"],
                description=d.get("description"),
                internship_type=d["type"],
                mode=d["mode"],
                stipend=d.get("stipend"),
                duration=d.get("duration"),
                location=d.get("location"),
                openings=d.get("openings", 1),
                application_start=d.get("app_start"),
                application_end=d.get("app_end"),
                eligibility_criteria=d.get("eligibility"),
                minimum_readiness_score=d.get("min_score", 0.0),
                minimum_cgpa=d.get("min_cgpa"),
                allowed_branches=d.get("branches"),
                official_apply_link=d.get("apply_link"),
                status="ACTIVE",
            ))
    await session.commit()

    for d in PLACEMENT_SEED:
        company = all_companies.get(d["company"])
        if not company:
            logger.warning(f"Placement seed skipped: company '{d['company']}' not found")
            continue
        existing = await session.execute(
            select(PlacementJob).where(
                PlacementJob.company_id == company.id,
                PlacementJob.title == d["title"],
            )
        )
        if not existing.scalars().first():
            session.add(PlacementJob(
                company_id=company.id,
                title=d["title"],
                description=d.get("description"),
                package_min=d.get("pkg_min"),
                package_max=d.get("pkg_max"),
                location=d.get("location"),
                bond=d.get("bond"),
                eligibility_criteria=d.get("eligibility"),
                minimum_readiness_score=d.get("min_score", 0.0),
                minimum_cgpa=d.get("min_cgpa"),
                allowed_branches=d.get("branches"),
                official_apply_link=d.get("apply_link"),
                deadline=d.get("deadline"),
                openings=d.get("openings", 1),
                status="ACTIVE",
            ))
    await session.commit()
    logger.info("Internship & Placement seed: done.")

    # 13. Gamification Master Data
    for l_data in LEVELS_SEED:
        existing = await session.execute(select(Level).where(Level.level_number == l_data["level_number"]))
        if not existing.scalars().first():
            session.add(Level(**l_data))

    for a_data in ACHIEVEMENTS_SEED:
        existing = await session.execute(select(Achievement).where(Achievement.code == a_data["code"]))
        if not existing.scalars().first():
            session.add(Achievement(**a_data))

    for b_data in BADGES_SEED:
        existing = await session.execute(select(Badge).where(Badge.code == b_data["code"]))
        if not existing.scalars().first():
            session.add(Badge(**b_data))

    today_date = date.today()
    for d_data in DAILY_CHALLENGES_SEED:
        existing = await session.execute(select(DailyChallenge).where(DailyChallenge.title == d_data["title"]))
        if not existing.scalars().first():
            session.add(DailyChallenge(expires_at=today_date + timedelta(days=1), **d_data))

    for w_data in WEEKLY_CHALLENGES_SEED:
        existing = await session.execute(select(WeeklyChallenge).where(WeeklyChallenge.title == w_data["title"]))
        if not existing.scalars().first():
            session.add(WeeklyChallenge(expires_at=today_date + timedelta(days=7), **w_data))

    for m_data in MONTHLY_CHALLENGES_SEED:
        existing = await session.execute(select(MonthlyChallenge).where(MonthlyChallenge.title == m_data["title"]))
        if not existing.scalars().first():
            session.add(MonthlyChallenge(expires_at=today_date + timedelta(days=30), **m_data))

    for r_data in REWARDS_SEED:
        existing = await session.execute(select(Reward).where(Reward.title == r_data["title"]))
        if not existing.scalars().first():
            session.add(Reward(**r_data))

    await session.commit()
    logger.info("Gamification Master Seed: done.")


async def init_db(engine: AsyncEngine) -> None:
    logger.info("Initializing database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        await seed_master_data(session)
    logger.info("Database initialized and seeded successfully.")

