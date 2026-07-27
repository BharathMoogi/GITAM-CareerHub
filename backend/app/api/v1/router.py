from fastapi import APIRouter
from app.api.v1.endpoints import (
    health, auth, students, masters, roadmaps, courses,
    projects, certifications, companies, placement, ai, dashboard, gamification, resume, notification, cms, monitoring
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health & System"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(students.router, prefix="/students", tags=["Student Profile"])
api_router.include_router(masters.router, tags=["Master Data"])
api_router.include_router(roadmaps.router, prefix="/roadmaps", tags=["Academic Roadmap Engine"])
api_router.include_router(courses.router, prefix="/courses", tags=["Learning Engine - Courses & Skills"])
api_router.include_router(projects.router, prefix="/projects", tags=["Project Intelligence Engine"])
api_router.include_router(certifications.router, prefix="/certifications", tags=["Certification Intelligence Engine"])
api_router.include_router(companies.router, prefix="/companies", tags=["Industry Intelligence Engine"])
api_router.include_router(placement.router, prefix="", tags=["Internship & Placement Engine"])
api_router.include_router(ai.router, prefix="", tags=["AI Mentor Engine"])
api_router.include_router(dashboard.router, prefix="", tags=["Dashboard Intelligence Engine"])
api_router.include_router(gamification.router, prefix="", tags=["Career Gamification Engine"])
api_router.include_router(resume.router, prefix="", tags=["Resume Intelligence Engine"])
api_router.include_router(notification.router, prefix="", tags=["Notification Engine"])
api_router.include_router(cms.router, prefix="", tags=["Enterprise Admin CMS"])
api_router.include_router(monitoring.router, prefix="", tags=["Health & System"])







