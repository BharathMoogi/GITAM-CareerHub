"""
AI Mentor Service — Core Orchestration Layer.

Workflow for every request:
  1. Validate student identity (auth)
  2. Load FULL student context from all 8 engines
  3. Render the appropriate Jinja2 prompt template
  4. Send to LLM provider (via factory)
  5. Persist the conversation to DB
  6. Return structured response (or stream)

No business logic in the API endpoints — everything lives here.
"""
import hashlib
import json
import logging
from datetime import date, datetime, timedelta, timezone
from typing import AsyncIterator, Dict, List, Optional, Any

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestException, NotFoundException, ForbiddenException
from app.ai.providers.base import ChatMessage, LLMConfig
from app.ai.providers.factory import LLMProviderFactory
from app.ai.prompts.engine import PromptEngine
from app.ai.context import StudentContext, StudentContextAggregator
from app.ai.rag.base import NoOpRetriever

logger = logging.getLogger("app.ai.mentor_service")

# Simple in-memory response cache: hash(student_id+tool+query) -> (response, timestamp)
_RESPONSE_CACHE: Dict[str, tuple] = {}
_CACHE_TTL_SECONDS = 300  # 5 minutes


class AIMentorService:
    """
    Central service for all AI Mentor operations.
    Injected into every API endpoint via FastAPI dependency.
    """

    def __init__(self, db: AsyncSession, provider_config: Optional[LLMConfig] = None):
        self.db = db
        self._provider = LLMProviderFactory.create(provider_config)
        self._prompt_engine = PromptEngine()
        self._aggregator = StudentContextAggregator(db)
        self._retriever = NoOpRetriever()  # Replaced when RAG is implemented

    # ── 1. Chat ───────────────────────────────────────────────────────────────

    async def chat(
        self,
        user_id: str,
        message: str,
        conversation_id: Optional[str] = None,
        tool: str = "career_advisor",
    ) -> Dict[str, Any]:
        """
        Send a message to the AI Mentor and get a complete response.
        Conversation history is maintained automatically.
        """
        from app.models.ai_mentor import Conversation, ConversationMessage

        # 1. Load or create conversation
        conversation = await self._get_or_create_conversation(user_id, conversation_id)

        # 2. Load complete student context
        ctx = await self._aggregator.load(user_id)

        # 3. Check cache
        cache_key = self._cache_key(ctx.student_id, tool, message)
        cached = self._get_cache(cache_key)
        if cached:
            logger.debug(f"Cache HIT for {cache_key[:16]}...")
            # Still save message to DB, return cached response
            await self._save_message(conversation.id, "user", message)
            await self._save_message(conversation.id, "assistant", cached, token_usage=0)
            return self._build_response(cached, conversation, ctx, cached=True)

        # 4. Build conversation history for this session
        history = await self._load_history(conversation.id)

        # 5. Render system prompt from template
        system_prompt = self._prompt_engine.render(
            self._resolve_tool_template(tool),
            **ctx.as_dict(),
            user_query=message,
        )

        # 6. Call LLM
        llm_messages = self._build_llm_messages(history, message)
        llm_response = await self._provider.chat(
            messages=llm_messages,
            system_prompt=system_prompt,
        )

        # 7. Persist conversation
        await self._save_message(conversation.id, "user", message)
        await self._save_message(
            conversation.id, "assistant",
            llm_response.content,
            token_usage=llm_response.token_usage,
        )

        # 8. Update conversation title if it's the first message
        if not history:
            await self._update_conversation_title(conversation, message[:80])

        # 9. Cache the response
        self._set_cache(cache_key, llm_response.content)

        # 10. Persist learning recommendation if tool suggests items
        await self._maybe_persist_recommendation(ctx.student_id, tool, llm_response.content)

        return self._build_response(llm_response.content, conversation, ctx)

    async def stream_chat(
        self,
        user_id: str,
        message: str,
        conversation_id: Optional[str] = None,
        tool: str = "career_advisor",
    ) -> AsyncIterator[str]:
        """
        Stream a response token-by-token using Server-Sent Events format.
        Each yielded chunk is formatted as: data: <token>\n\n
        """
        from app.models.ai_mentor import Conversation, ConversationMessage

        conversation = await self._get_or_create_conversation(user_id, conversation_id)
        ctx = await self._aggregator.load(user_id)
        history = await self._load_history(conversation.id)

        system_prompt = self._prompt_engine.render(
            self._resolve_tool_template(tool),
            **ctx.as_dict(),
            user_query=message,
        )

        llm_messages = self._build_llm_messages(history, message)
        await self._save_message(conversation.id, "user", message)

        full_response = []
        yield f"data: {json.dumps({'type': 'start', 'conversation_id': conversation.id})}\n\n"

        async for token in self._provider.stream(messages=llm_messages, system_prompt=system_prompt):
            full_response.append(token)
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        complete = "".join(full_response)
        await self._save_message(conversation.id, "assistant", complete)
        yield f"data: {json.dumps({'type': 'done', 'total_chars': len(complete)})}\n\n"

    # ── 2. Conversations ──────────────────────────────────────────────────────

    async def list_conversations(self, user_id: str) -> List[Dict]:
        from app.models.ai_mentor import Conversation
        from app.models.student import Student

        stu_res = await self.db.execute(select(Student).where(Student.user_id == user_id))
        student = stu_res.scalars().first()
        if not student:
            raise NotFoundException("Student profile not found")

        res = await self.db.execute(
            select(Conversation)
            .where(Conversation.student_id == student.id)
            .order_by(desc(Conversation.updated_at))
            .limit(50)
        )
        convos = res.scalars().all()
        return [{"id": c.id, "title": c.title, "updated_at": c.updated_at.isoformat()} for c in convos]

    async def get_conversation_messages(self, user_id: str, conversation_id: str) -> List[Dict]:
        from app.models.ai_mentor import Conversation, ConversationMessage

        convo = await self._get_conversation_or_404(conversation_id)
        await self._assert_convo_owner(user_id, convo)

        res = await self.db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at)
        )
        msgs = res.scalars().all()
        return [{"id": m.id, "role": m.role, "message": m.message, "created_at": m.created_at.isoformat()} for m in msgs]

    async def delete_conversation(self, user_id: str, conversation_id: str) -> None:
        from app.models.ai_mentor import Conversation

        convo = await self._get_conversation_or_404(conversation_id)
        await self._assert_convo_owner(user_id, convo)
        await self.db.delete(convo)
        await self.db.commit()

    # ── 3. Weekly Plan ────────────────────────────────────────────────────────

    async def generate_weekly_plan(self, user_id: str) -> Dict[str, Any]:
        from app.models.ai_mentor import WeeklyPlan

        ctx = await self._aggregator.load(user_id)
        today = date.today()
        week_start = today - timedelta(days=today.weekday())  # Monday

        # Check if plan already exists for this week
        existing = await self.db.execute(
            select(WeeklyPlan).where(
                WeeklyPlan.student_id == ctx.student_id,
                WeeklyPlan.week_start == week_start,
            )
        )
        if plan := existing.scalars().first():
            import json as _json
            return {
                "id": plan.id,
                "week_start": str(plan.week_start),
                "tasks": _json.loads(plan.tasks_json),
                "estimated_hours": plan.estimated_hours,
                "completion_percentage": plan.completion_percentage,
                "cached": True,
            }

        system_prompt = self._prompt_engine.render(
            "weekly_planner",
            **ctx.as_dict(),
            week_start=str(week_start),
            user_query="Generate my weekly plan based on my current goals and gaps.",
        )
        llm_response = await self._provider.chat(
            messages=[ChatMessage(role="user", content="Generate my weekly study plan")],
            system_prompt=system_prompt,
        )

        # Parse response into structured tasks
        tasks = self._parse_weekly_tasks(llm_response.content)

        plan = WeeklyPlan(
            student_id=ctx.student_id,
            week_start=week_start,
            tasks_json=json.dumps(tasks),
            estimated_hours=sum(t.get("hours", 2) for t in tasks),
            completion_percentage=0.0,
        )
        self.db.add(plan)
        await self.db.commit()
        await self.db.refresh(plan)

        return {
            "id": plan.id,
            "week_start": str(week_start),
            "tasks": tasks,
            "estimated_hours": plan.estimated_hours,
            "completion_percentage": 0.0,
            "ai_narrative": llm_response.content,
        }

    # ── 4. Recommendations ────────────────────────────────────────────────────

    async def get_project_suggestions(self, user_id: str) -> Dict[str, Any]:
        ctx = await self._aggregator.load(user_id)
        system_prompt = self._prompt_engine.render(
            "project_recommender", **ctx.as_dict(),
            user_query="Which projects should I work on to maximize my career readiness?",
        )
        resp = await self._provider.chat(
            messages=[ChatMessage(role="user", content="Suggest projects for me")],
            system_prompt=system_prompt,
        )
        return {
            "recommended_projects": [
                {"id": p.id, "title": p.title, "type": p.project_type, "difficulty": p.difficulty}
                for p in ctx.recommended_projects[:5]
            ],
            "ai_analysis": resp.content,
            "student_skills": [{"name": s.name, "score": s.score} for s in ctx.skills[:8]],
        }

    async def get_course_suggestions(self, user_id: str) -> Dict[str, Any]:
        ctx = await self._aggregator.load(user_id)
        system_prompt = self._prompt_engine.render(
            "learning_planner", **ctx.as_dict(),
            user_query="What courses should I take next to close my skill gaps?",
        )
        resp = await self._provider.chat(
            messages=[ChatMessage(role="user", content="Suggest courses for me")],
            system_prompt=system_prompt,
        )
        return {
            "recommended_courses": [
                {"title": c.title, "platform": c.platform, "hours": c.estimated_hours, "difficulty": c.difficulty}
                for c in ctx.recommended_courses[:6]
            ],
            "ai_analysis": resp.content,
            "skill_gaps": ctx.skill_gaps[:5],
        }

    async def get_certification_suggestions(self, user_id: str) -> Dict[str, Any]:
        ctx = await self._aggregator.load(user_id)
        system_prompt = self._prompt_engine.render(
            "certification_recommender", **ctx.as_dict(),
            user_query="Which certifications are most valuable for my career path?",
        )
        resp = await self._provider.chat(
            messages=[ChatMessage(role="user", content="Suggest certifications for me")],
            system_prompt=system_prompt,
        )
        return {
            "recommended_certifications": [
                {"id": c.id, "title": c.title, "provider": c.provider, "hours": c.estimated_hours}
                for c in ctx.recommended_certifications[:5]
            ],
            "completed_certifications": [
                {"title": c.title, "provider": c.provider}
                for c in ctx.completed_certifications
            ],
            "ai_analysis": resp.content,
        }

    async def get_company_readiness(self, user_id: str) -> Dict[str, Any]:
        ctx = await self._aggregator.load(user_id)
        system_prompt = self._prompt_engine.render(
            "company_readiness", **ctx.as_dict(),
            user_query="Give me a detailed readiness analysis for my target companies.",
        )
        resp = await self._provider.chat(
            messages=[ChatMessage(role="user", content="Analyse my company readiness")],
            system_prompt=system_prompt,
        )
        return {
            "readiness_scores": [
                {
                    "company": r.company_name,
                    "overall": r.overall_score,
                    "skill": r.skill_score,
                    "project": r.project_score,
                    "cert": r.cert_score,
                    "status": "Ready" if r.overall_score >= 70 else "Almost Ready" if r.overall_score >= 50 else "Needs Work",
                }
                for r in ctx.readiness_scores
            ],
            "avg_readiness": ctx.avg_readiness_score,
            "top_company": ctx.top_company,
            "ai_analysis": resp.content,
        }

    async def get_interview_prep(self, user_id: str) -> Dict[str, Any]:
        ctx = await self._aggregator.load(user_id)
        system_prompt = self._prompt_engine.render(
            "interview_coach", **ctx.as_dict(),
            user_query="Create a comprehensive interview preparation plan for my target companies.",
        )
        resp = await self._provider.chat(
            messages=[ChatMessage(role="user", content="Prepare me for interviews")],
            system_prompt=system_prompt,
        )
        return {
            "target_role": ctx.target_role,
            "goals": [{"type": g.goal_type, "value": g.goal_value} for g in ctx.goals],
            "projects_for_resume": [
                {"title": p.title, "type": p.project_type}
                for p in ctx.completed_projects
            ],
            "certifications": [
                {"title": c.title, "provider": c.provider}
                for c in ctx.completed_certifications
            ],
            "ai_prep_plan": resp.content,
        }

    # ── 5. Goals ──────────────────────────────────────────────────────────────

    async def set_goal(
        self,
        user_id: str,
        goal_type: str,
        goal_value: str,
        target_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        from app.models.ai_mentor import StudentGoal
        from app.models.student import Student

        valid_types = {"TARGET_COMPANY", "TARGET_ROLE", "HIGHER_STUDIES", "RESEARCH", "ENTREPRENEURSHIP"}
        if goal_type not in valid_types:
            raise BadRequestException(f"Invalid goal_type. Must be one of: {', '.join(valid_types)}")

        stu_res = await self.db.execute(select(Student).where(Student.user_id == user_id))
        student = stu_res.scalars().first()
        if not student:
            raise NotFoundException("Student profile not found")

        goal = StudentGoal(
            student_id=student.id,
            goal_type=goal_type,
            goal_value=goal_value,
            target_date=target_date,
            status="ACTIVE",
        )
        self.db.add(goal)
        await self.db.commit()
        await self.db.refresh(goal)

        logger.info(f"Goal set: {goal_type} = {goal_value} for student {student.id}")
        return {
            "id": goal.id,
            "goal_type": goal.goal_type,
            "goal_value": goal.goal_value,
            "target_date": str(goal.target_date) if goal.target_date else None,
            "status": goal.status,
            "message": f"Goal set successfully! I'll tailor all my recommendations to help you achieve: {goal_value}",
        }

    async def list_goals(self, user_id: str) -> List[Dict]:
        from app.models.ai_mentor import StudentGoal
        from app.models.student import Student

        stu_res = await self.db.execute(select(Student).where(Student.user_id == user_id))
        student = stu_res.scalars().first()
        if not student:
            raise NotFoundException("Student profile not found")

        res = await self.db.execute(
            select(StudentGoal)
            .where(StudentGoal.student_id == student.id)
            .order_by(desc(StudentGoal.created_at))
        )
        return [
            {
                "id": g.id, "goal_type": g.goal_type, "goal_value": g.goal_value,
                "target_date": str(g.target_date) if g.target_date else None,
                "status": g.status, "created_at": g.created_at.isoformat(),
            }
            for g in res.scalars().all()
        ]

    async def update_goal_status(self, user_id: str, goal_id: str, status: str) -> Dict:
        from app.models.ai_mentor import StudentGoal

        valid = {"ACTIVE", "ACHIEVED", "DROPPED"}
        if status not in valid:
            raise BadRequestException(f"Invalid status. Must be one of: {', '.join(valid)}")

        res = await self.db.execute(select(StudentGoal).where(StudentGoal.id == goal_id))
        goal = res.scalars().first()
        if not goal:
            raise NotFoundException("Goal not found")

        await self._assert_goal_owner(user_id, goal)
        goal.status = status
        goal.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        return {"id": goal.id, "status": goal.status, "message": "Goal updated"}

    # ── 6. Provider health ────────────────────────────────────────────────────

    async def get_provider_info(self) -> Dict[str, Any]:
        return {
            "provider": self._provider.provider_name,
            "model": self._provider.config.model,
            "available": await self._provider.is_available(),
            "available_providers": LLMProviderFactory.available_providers(),
            "templates": self._prompt_engine.list_templates(),
            "rag_status": "NoOpRetriever (RAG not yet configured)",
        }

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _get_or_create_conversation(self, user_id: str, conversation_id: Optional[str]):
        from app.models.ai_mentor import Conversation
        from app.models.student import Student

        if conversation_id:
            res = await self.db.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            convo = res.scalars().first()
            if convo:
                return convo
            raise NotFoundException(f"Conversation {conversation_id} not found")

        stu_res = await self.db.execute(select(Student).where(Student.user_id == user_id))
        student = stu_res.scalars().first()
        if not student:
            raise NotFoundException("Student profile not found")

        convo = Conversation(student_id=student.id, title="New Conversation")
        self.db.add(convo)
        await self.db.flush()
        return convo

    async def _load_history(self, conversation_id: str) -> List[ChatMessage]:
        from app.models.ai_mentor import ConversationMessage

        res = await self.db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at)
            .limit(20)   # Last 20 messages for context window
        )
        messages = []
        for m in res.scalars().all():
            if m.role in ("user", "assistant"):
                messages.append(ChatMessage(role=m.role, content=m.message))
        return messages

    def _build_llm_messages(self, history: List[ChatMessage], user_message: str) -> List[ChatMessage]:
        msgs = list(history)
        msgs.append(ChatMessage(role="user", content=user_message))
        return msgs

    async def _save_message(
        self, conversation_id: str, role: str, message: str, token_usage: Optional[int] = None
    ) -> None:
        from app.models.ai_mentor import ConversationMessage, Conversation

        msg = ConversationMessage(
            conversation_id=conversation_id,
            role=role,
            message=message,
            token_usage=token_usage,
        )
        self.db.add(msg)

        # Update conversation updated_at
        res = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        if convo := res.scalars().first():
            convo.updated_at = datetime.now(timezone.utc)

        await self.db.commit()

    async def _update_conversation_title(self, conversation, title: str) -> None:
        from app.models.ai_mentor import Conversation

        res = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation.id)
        )
        if convo := res.scalars().first():
            convo.title = title.strip()[:100] if title.strip() else "New Conversation"
            await self.db.commit()

    async def _get_conversation_or_404(self, conversation_id: str):
        from app.models.ai_mentor import Conversation

        res = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        convo = res.scalars().first()
        if not convo:
            raise NotFoundException(f"Conversation {conversation_id} not found")
        return convo

    async def _assert_convo_owner(self, user_id: str, convo) -> None:
        from app.models.student import Student

        stu_res = await self.db.execute(select(Student).where(Student.user_id == user_id))
        student = stu_res.scalars().first()
        if not student or student.id != convo.student_id:
            raise ForbiddenException("You don't have access to this conversation")

    async def _assert_goal_owner(self, user_id: str, goal) -> None:
        from app.models.student import Student

        stu_res = await self.db.execute(select(Student).where(Student.user_id == user_id))
        student = stu_res.scalars().first()
        if not student or student.id != goal.student_id:
            raise ForbiddenException("You don't have access to this goal")

    def _resolve_tool_template(self, tool: str) -> str:
        """Map tool name to prompt template filename."""
        mapping = {
            "career_advisor": "career_advisor",
            "roadmap_advisor": "roadmap_advisor",
            "project_recommender": "project_recommender",
            "certification_recommender": "certification_recommender",
            "company_readiness": "company_readiness",
            "skill_gap_analyzer": "skill_gap_analyzer",
            "resume_advisor": "resume_advisor",
            "interview_coach": "interview_coach",
            "learning_planner": "learning_planner",
            "weekly_planner": "weekly_planner",
        }
        return mapping.get(tool, "career_advisor")

    def _build_response(self, content: str, conversation, ctx: StudentContext, cached: bool = False) -> Dict:
        return {
            "conversation_id": conversation.id,
            "response": content,
            "student_name": ctx.student_name,
            "context_loaded": True,
            "cached": cached,
            "provider": self._provider.provider_name,
        }

    def _cache_key(self, student_id: str, tool: str, query: str) -> str:
        raw = f"{student_id}:{tool}:{query}"
        return hashlib.md5(raw.encode()).hexdigest()

    def _get_cache(self, key: str) -> Optional[str]:
        if key in _RESPONSE_CACHE:
            content, ts = _RESPONSE_CACHE[key]
            if (datetime.now(timezone.utc) - ts).seconds < _CACHE_TTL_SECONDS:
                return content
            del _RESPONSE_CACHE[key]
        return None

    def _set_cache(self, key: str, content: str) -> None:
        _RESPONSE_CACHE[key] = (content, datetime.now(timezone.utc))

    def _parse_weekly_tasks(self, ai_response: str) -> List[Dict]:
        """Parse AI weekly plan response into a structured task list."""
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        tasks = []
        lines = ai_response.split("\n")
        for line in lines:
            for day in days:
                if day in line and ":" in line:
                    tasks.append({
                        "day": day,
                        "task": line.split(":", 1)[-1].strip()[:300],
                        "hours": 2,  # Default, AI response may specify
                    })
                    break
        # Fallback if parsing fails
        if not tasks:
            for day in days[:5]:
                tasks.append({"day": day, "task": "Study + project work", "hours": 3})
        return tasks

    async def _maybe_persist_recommendation(
        self, student_id: str, tool: str, ai_response: str
    ) -> None:
        """Persist a LearningRecommendation record for trackable tools."""
        from app.models.ai_mentor import LearningRecommendation

        tool_to_rec_type = {
            "project_recommender": "PROJECT",
            "certification_recommender": "CERTIFICATION",
            "learning_planner": "COURSE",
            "interview_coach": "INTERVIEW",
        }
        rec_type = tool_to_rec_type.get(tool)
        if not rec_type:
            return

        rec = LearningRecommendation(
            student_id=student_id,
            recommendation_type=rec_type,
            item_title=f"AI {tool.replace('_', ' ').title()} recommendation",
            priority=1,
            reason=ai_response[:500],
        )
        self.db.add(rec)
        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()
