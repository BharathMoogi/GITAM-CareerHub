"""
Resume Intelligence Engine — REST API Endpoints.

Routes:
  GET  /resume                → Fetch full resume profile
  POST /resume                → Update headline and summary
  POST /resume/experience     → Add work / internship experience
  POST /resume/hackathon      → Add hackathon achievement
  POST /resume/publication    → Add research publication
  POST /resume/patent         → Add patent record
  POST /resume/generate       → Generate structured ATS Resume JSON & PDF Layout Metadata
  POST /resume/review         → AI Resume Review, Bullet Improvement & STAR Bullet Generator
  GET  /resume/score          → Live ATS Score, Resume Score, Portfolio Score & Missing Keywords
  GET  /portfolio             → Get personal portfolio website JSON
  POST /portfolio/review      → AI Portfolio Review & Design Feedback
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.services.resume_service import ResumeService
from app.schemas.resume import (
    ResumeHeaderUpdate, ResumeProfileResponse, GenerateATSResponse,
    ResumeReviewRequest, ResumeReviewResponse, ResumeScoreResponse,
    PortfolioJSONResponse, PortfolioReviewResponse,
    AddExperienceRequest, AddHackathonRequest, AddPublicationRequest, AddPatentRequest
)

logger = logging.getLogger("app.api.resume")
router = APIRouter()


# ── 1. Resume Profile Endpoints ───────────────────────────────────────────────

@router.get(
    "/resume",
    response_model=ResumeProfileResponse,
    summary="Get My Resume Profile",
    description="Returns full student resume profile including work experience, publications, patents, and hackathons.",
)
async def get_resume(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    result = await service.get_or_create_resume(user_id=current_user.id)
    return ResumeProfileResponse(**result)


@router.post(
    "/resume",
    response_model=ResumeProfileResponse,
    summary="Update Headline & Summary",
    description="Updates top-level resume headline and professional summary.",
)
async def update_resume_header(
    request: ResumeHeaderUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    result = await service.update_resume_header(
        user_id=current_user.id,
        headline=request.headline,
        summary=request.summary,
    )
    return ResumeProfileResponse(**result)


@router.post(
    "/resume/experience",
    summary="Add Work / Internship Experience",
    description="Adds a new work or internship experience entry.",
)
async def add_experience(
    request: AddExperienceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    return await service.add_experience(
        user_id=current_user.id,
        company_name=request.company_name,
        role_title=request.role_title,
        start_date=request.start_date,
        end_date=request.end_date,
        is_current=request.is_current,
        location=request.location,
        bullet_points=request.bullet_points,
    )


@router.post(
    "/resume/hackathon",
    summary="Add Hackathon Entry",
    description="Adds a hackathon win or participation entry.",
)
async def add_hackathon(
    request: AddHackathonRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    return await service.add_hackathon(
        user_id=current_user.id,
        event_name=request.event_name,
        project_title=request.project_title,
        prize_rank=request.prize_rank,
        date_held=request.date_held,
        repo_url=request.repo_url,
    )


@router.post(
    "/resume/publication",
    summary="Add Research Publication",
    description="Adds a research paper publication entry.",
)
async def add_publication(
    request: AddPublicationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    return await service.add_publication(
        user_id=current_user.id,
        title=request.title,
        journal_publisher=request.journal_publisher,
        publication_date=request.publication_date,
        paper_url=request.paper_url,
        authors=request.authors,
    )


@router.post(
    "/resume/patent",
    summary="Add Patent Entry",
    description="Adds a patent record.",
)
async def add_patent(
    request: AddPatentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    return await service.add_patent(
        user_id=current_user.id,
        title=request.title,
        patent_number=request.patent_number,
        filing_date=request.filing_date,
        status=request.status,
        url=request.url,
    )


# ── 2. ATS Generation & Scores ────────────────────────────────────────────────

@router.post(
    "/resume/generate",
    response_model=GenerateATSResponse,
    summary="Generate ATS Resume JSON & PDF Metadata",
    description="Generates complete ATS-parseable Resume JSON, PDF layout metadata, ATS scores, missing keywords, and recommended improvements.",
)
async def generate_ats_resume(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    result = await service.generate_ats_resume_json(user_id=current_user.id)
    return GenerateATSResponse(**result)


@router.post(
    "/resume/review",
    response_model=ResumeReviewResponse,
    summary="AI Resume Review & STAR Bullet Rewrite",
    description="AI analyzes resume content and generates high-impact STAR-format bullet rewrites.",
)
async def review_resume_ai(
    request: Optional[ResumeReviewRequest] = Body(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    jd = request.job_description if request else None
    result = await service.review_resume_ai(user_id=current_user.id, job_description=jd)
    return ResumeReviewResponse(**result)


@router.get(
    "/resume/score",
    response_model=ResumeScoreResponse,
    summary="Get Resume & ATS Score Analysis",
    description="Returns live ATS score, overall resume score, portfolio score, missing target role keywords, and recommendations.",
)
async def get_resume_score(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    result = await service.get_resume_score(user_id=current_user.id)
    return ResumeScoreResponse(**result)


# ── 3. Portfolio Endpoints ────────────────────────────────────────────────────

@router.get(
    "/portfolio",
    response_model=PortfolioJSONResponse,
    summary="Get Portfolio Website JSON",
    description="Generates personal portfolio website structure JSON showcasing skills, featured projects, certifications, and bio.",
)
async def get_portfolio(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    result = await service.get_portfolio_json(user_id=current_user.id)
    return PortfolioJSONResponse(**result)


@router.post(
    "/portfolio/review",
    response_model=PortfolioReviewResponse,
    summary="AI Portfolio Review",
    description="AI evaluates portfolio structure, presentation, and suggests design improvements.",
)
async def review_portfolio_ai(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    result = await service.review_portfolio_ai(user_id=current_user.id)
    return PortfolioReviewResponse(**result)
