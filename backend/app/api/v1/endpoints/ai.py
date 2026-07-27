"""
AI Mentor Engine — REST API Endpoints.

All endpoints follow the rule: student context is ALWAYS loaded from
the database before generating any AI response.

Routes:
  POST   /ai/chat                     — Conversational AI (with/without streaming)
  GET    /ai/conversations            — List student's conversations
  GET    /ai/conversations/{id}       — Get conversation messages
  DELETE /ai/conversations/{id}       — Delete a conversation
  GET    /ai/weekly-plan              — Generate / retrieve this week's plan
  GET    /ai/project-suggestions      — AI project recommendations
  GET    /ai/course-suggestions       — AI course recommendations
  GET    /ai/certification-suggestions— AI certification recommendations
  GET    /ai/company-readiness        — Company readiness analysis
  GET    /ai/interview-prep           — Interview preparation plan
  POST   /ai/set-goal                 — Set a career goal
  GET    /ai/goals                    — List all goals
  PATCH  /ai/goals/{id}               — Update goal status
  GET    /ai/provider-info            — LLM provider health check
"""
import logging
from typing import List

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.services.ai_mentor_service import AIMentorService
from app.schemas.ai_mentor import (
    ChatRequest, ChatResponse,
    ConversationSummary, MessageRead,
    GoalCreateRequest, GoalCreateResponse, GoalRead, GoalStatusUpdate,
    WeeklyPlanResponse,
    ProjectSuggestionResponse, CourseSuggestionResponse,
    CertificationSuggestionResponse, CompanyReadinessResponse,
    InterviewPrepResponse, ProviderInfoResponse,
)

logger = logging.getLogger("app.api.ai")
router = APIRouter()


def _service(
    db: AsyncSession = Depends(get_db),
) -> AIMentorService:
    """FastAPI dependency that constructs the AIMentorService."""
    return AIMentorService(db)


# ── Chat ──────────────────────────────────────────────────────────────────────

@router.post(
    "/ai/chat",
    response_model=ChatResponse,
    summary="Chat with the AI Mentor",
    description=(
        "Send a message to the AI Career Mentor. The AI always loads your complete student profile "
        "(roadmap, skills, projects, certifications, readiness, applications, goals) before responding. "
        "Set `stream=true` to receive a streaming response via Server-Sent Events."
    ),
)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AIMentorService(db)

    if request.stream:
        return StreamingResponse(
            service.stream_chat(
                user_id=current_user.id,
                message=request.message,
                conversation_id=request.conversation_id,
                tool=request.tool,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    result = await service.chat(
        user_id=current_user.id,
        message=request.message,
        conversation_id=request.conversation_id,
        tool=request.tool,
    )
    return ChatResponse(**result)


# ── Conversations ─────────────────────────────────────────────────────────────

@router.get(
    "/ai/conversations",
    response_model=List[ConversationSummary],
    summary="List my conversations",
)
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AIMentorService(db)
    convos = await service.list_conversations(user_id=current_user.id)
    return [ConversationSummary(**c) for c in convos]


@router.get(
    "/ai/conversations/{conversation_id}",
    response_model=List[MessageRead],
    summary="Get conversation messages",
)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AIMentorService(db)
    msgs = await service.get_conversation_messages(
        user_id=current_user.id,
        conversation_id=conversation_id,
    )
    return [MessageRead(**m) for m in msgs]


@router.delete(
    "/ai/conversations/{conversation_id}",
    summary="Delete a conversation",
    status_code=204,
)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AIMentorService(db)
    await service.delete_conversation(
        user_id=current_user.id,
        conversation_id=conversation_id,
    )


# ── Weekly Plan ───────────────────────────────────────────────────────────────

@router.get(
    "/ai/weekly-plan",
    response_model=WeeklyPlanResponse,
    summary="Generate / retrieve this week's AI study plan",
    description=(
        "Generates a personalised 7-day study plan based on your pending roadmap modules, "
        "skill gaps, and active goals. Returns cached plan if one exists for this week."
    ),
)
async def get_weekly_plan(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AIMentorService(db)
    result = await service.generate_weekly_plan(user_id=current_user.id)
    return WeeklyPlanResponse(**result)


# ── Recommendations ───────────────────────────────────────────────────────────

@router.get(
    "/ai/project-suggestions",
    response_model=ProjectSuggestionResponse,
    summary="AI project recommendations",
    description="Returns AI-ranked project suggestions matched to your skills and target companies.",
)
async def project_suggestions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AIMentorService(db)
    result = await service.get_project_suggestions(user_id=current_user.id)
    return ProjectSuggestionResponse(**result)


@router.get(
    "/ai/course-suggestions",
    response_model=CourseSuggestionResponse,
    summary="AI course recommendations",
    description="Returns courses to close your skill gaps, ordered by career impact.",
)
async def course_suggestions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AIMentorService(db)
    result = await service.get_course_suggestions(user_id=current_user.id)
    return CourseSuggestionResponse(**result)


@router.get(
    "/ai/certification-suggestions",
    response_model=CertificationSuggestionResponse,
    summary="AI certification recommendations",
    description="Returns certifications by career ROI — free options like NPTEL highlighted.",
)
async def certification_suggestions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AIMentorService(db)
    result = await service.get_certification_suggestions(user_id=current_user.id)
    return CertificationSuggestionResponse(**result)


@router.get(
    "/ai/company-readiness",
    response_model=CompanyReadinessResponse,
    summary="Company readiness analysis",
    description=(
        "Analyses your readiness score for each company and generates a targeted improvement plan "
        "for your highest-priority target company."
    ),
)
async def company_readiness(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AIMentorService(db)
    result = await service.get_company_readiness(user_id=current_user.id)
    return CompanyReadinessResponse(**result)


@router.get(
    "/ai/interview-prep",
    response_model=InterviewPrepResponse,
    summary="Interview preparation plan",
    description=(
        "Generates a personalised interview prep plan using your actual projects as talking points, "
        "with questions tailored to your target companies."
    ),
)
async def interview_prep(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AIMentorService(db)
    result = await service.get_interview_prep(user_id=current_user.id)
    return InterviewPrepResponse(**result)


# ── Goals ─────────────────────────────────────────────────────────────────────

@router.post(
    "/ai/set-goal",
    response_model=GoalCreateResponse,
    status_code=201,
    summary="Set a career goal",
    description=(
        "Set a career goal that the AI Mentor uses to personalise ALL its recommendations. "
        "Goal types: TARGET_COMPANY, TARGET_ROLE, HIGHER_STUDIES, RESEARCH, ENTREPRENEURSHIP"
    ),
)
async def set_goal(
    request: GoalCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AIMentorService(db)
    result = await service.set_goal(
        user_id=current_user.id,
        goal_type=request.goal_type,
        goal_value=request.goal_value,
        target_date=request.target_date,
    )
    return GoalCreateResponse(**result)


@router.get(
    "/ai/goals",
    response_model=List[GoalRead],
    summary="List my career goals",
)
async def list_goals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AIMentorService(db)
    goals = await service.list_goals(user_id=current_user.id)
    return [GoalRead(**g) for g in goals]


@router.patch(
    "/ai/goals/{goal_id}",
    response_model=GoalRead,
    summary="Update goal status (ACTIVE / ACHIEVED / DROPPED)",
)
async def update_goal(
    goal_id: str,
    request: GoalStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AIMentorService(db)
    result = await service.update_goal_status(
        user_id=current_user.id,
        goal_id=goal_id,
        status=request.status,
    )
    return GoalRead(**result)


# ── Provider Info ─────────────────────────────────────────────────────────────

@router.get(
    "/ai/provider-info",
    response_model=ProviderInfoResponse,
    summary="LLM provider health and configuration",
    description="Returns the active LLM provider, model, health status, and available prompt templates.",
)
async def provider_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AIMentorService(db)
    result = await service.get_provider_info()
    return ProviderInfoResponse(**result)
