from app.database.base import Base
from app.models.user import User
from app.models.branch import Branch
from app.models.target_role import TargetRole
from app.models.student import Student
from app.models.academic_year import AcademicYear
from app.models.semester import Semester
from app.models.roadmap import Roadmap
from app.models.roadmap_module import RoadmapModule
from app.models.roadmap_dependency import RoadmapModuleDependency
from app.models.student_progress import StudentRoadmapProgress
from app.models.skill import Skill
from app.models.course import Course
from app.models.course_resource import CourseResource
from app.models.course_outcome import CourseOutcome
from app.models.course_skill import CourseSkill
from app.models.student_course_progress import StudentCourseProgress
from app.models.student_skill import StudentSkill
from app.models.project_technology import ProjectTechnology
from app.models.project import Project
from app.models.project_skill import ProjectSkill, ProjectTechnologyMap
from app.models.project_content import (
    ProjectResource, ProjectDeliverable,
    ProjectInterviewQuestion, ProjectResumePoint,
)
from app.models.student_project import StudentProject
from app.models.certification import Certification
from app.models.certification_skill import CertificationSkill, CertificationPrerequisite
from app.models.certification_content import CertificationExam, CertificationBenefit
from app.models.student_certification import StudentCertification
from app.models.company import Company
from app.models.job_role import JobRole
from app.models.company_mapping import CompanySkill, CompanyCourse, CompanyProject, CompanyCertification
from app.models.company_interview import CompanyInterviewRound, CompanyInterviewQuestion
from app.models.student_company_readiness import StudentCompanyReadiness
from app.models.placement import Internship, PlacementJob, StudentApplication, InterviewSchedule, OfferLetter
from app.models.ai_mentor import Conversation, ConversationMessage, StudentGoal, WeeklyPlan, LearningRecommendation
from app.models.gamification import Level, Achievement, Badge, StudentBadge, StudentXP, DailyChallenge, WeeklyChallenge, MonthlyChallenge, Reward, CareerMilestone
from app.models.resume import Resume, ResumeVersion, Portfolio, PortfolioSection, Experience, Achievements, Volunteer, Publication, Patent, Hackathon
from app.models.notification import Notification, Announcement, EmailQueue, NotificationTemplate, NotificationPreference, NotificationDeliveryLog
from app.models.cms import AuditLog, ApprovalRequest, ContentVersion, CmsBlog, CmsEvent, CmsResource






__all__ = [
    "Base", "User", "Branch", "TargetRole", "Student",
    "AcademicYear", "Semester",
    "Roadmap", "RoadmapModule", "RoadmapModuleDependency", "StudentRoadmapProgress",
    "Skill", "Course", "CourseResource", "CourseOutcome", "CourseSkill",
    "StudentCourseProgress", "StudentSkill",
    "ProjectTechnology", "Project", "ProjectSkill", "ProjectTechnologyMap",
    "ProjectResource", "ProjectDeliverable", "ProjectInterviewQuestion", "ProjectResumePoint",
    "StudentProject",
    "Certification", "CertificationSkill", "CertificationPrerequisite",
    "CertificationExam", "CertificationBenefit", "StudentCertification",
    "Company", "JobRole", "CompanySkill", "CompanyCourse", "CompanyProject", "CompanyCertification",
    "CompanyInterviewRound", "CompanyInterviewQuestion", "StudentCompanyReadiness",
    "Internship", "PlacementJob", "StudentApplication", "InterviewSchedule", "OfferLetter",
]
