"""
Tests for the AI Mentor Engine.

Covers:
  1.  Provider factory creates correct provider type
  2.  Mock provider returns deterministic responses
  3.  Mock provider streaming works
  4.  Provider is_available() returns True for mock
  5.  PromptEngine renders templates correctly
  6.  PromptEngine lists available templates
  7.  PromptEngine fallback when template missing
  8.  StudentContextAggregator raises 404 for unknown user
  9.  StudentContextAggregator loads minimal context
  10. Chat creates conversation and persists messages
  11. Chat returns cached response on second identical call
  12. Conversation persistence across multiple messages
  13. Goal creation with valid type
  14. Goal creation with invalid type raises 400
  15. Goal status update: ACHIEVED
  16. Goal ownership enforcement (ForbiddenException)
  17. Weekly plan generation and caching
  18. Project suggestions load student context
  19. Course suggestions return skill gaps
  20. Company readiness returns scores
  21. Interview prep loads completed projects
  22. Streaming chat yields tokens
  23. delete_conversation removes from DB
  24. Authorization: unauthenticated request raises 401
"""
import sys
import asyncio
import json
from datetime import date, datetime, timezone
from typing import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, async_sessionmaker

# Stub pytest
import types as _types
_pytest = _types.ModuleType("pytest")
class _RaisesCtx:
    def __init__(self, exc): self.exc = exc
    def __enter__(self): return self
    def __exit__(self, et, ev, tb):
        if et is None: raise AssertionError(f"Expected {self.exc.__name__} not raised")
        return issubclass(et, self.exc)
_pytest.raises = lambda exc: _RaisesCtx(exc)
sys.modules.setdefault("pytest", _pytest)

from app.models.user import User
from app.models.student import Student
from app.models.branch import Branch
from app.models.target_role import TargetRole
from app.models.ai_mentor import Conversation, ConversationMessage, StudentGoal, WeeklyPlan
from app.ai.providers.base import LLMConfig, ChatMessage
from app.ai.providers.factory import LLMProviderFactory
from app.ai.providers.mock import MockLLMProvider
from app.ai.prompts.engine import PromptEngine
from app.core.exceptions import BadRequestException, NotFoundException, ForbiddenException
from app.services.ai_mentor_service import AIMentorService
from app.schemas.ai_mentor import ChatRequest, GoalCreateRequest


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _make_branch(db, code="AIML"):
    res = await db.execute(select(Branch).where(Branch.code == code))
    b = res.scalars().first()
    if b: return b
    b = Branch(code=code, name=f"{code} Branch", description="Test")
    db.add(b); await db.commit(); await db.refresh(b)
    return b

async def _make_target_role(db):
    res = await db.execute(select(TargetRole))
    r = res.scalars().first()
    if r: return r
    r = TargetRole(title="ML Engineer", description="Test role")
    db.add(r); await db.commit(); await db.refresh(r)
    return r

async def _make_user_student(db, email="ai.test@gitam.edu", branch="AIML"):
    import uuid
    b = await _make_branch(db, branch)
    role = await _make_target_role(db)
    user = User(email=email, hashed_password="hash", is_active=True, role="STUDENT")
    db.add(user); await db.flush()
    student = Student(
        user_id=user.id, full_name="AI Test Student", email=email,
        roll_number=f"R{uuid.uuid4().hex[:8].upper()}",
        branch_id=b.id, target_role_id=role.id,
        current_year=3, semester=5, is_active=True,
    )
    db.add(student); await db.commit()
    await db.refresh(user); await db.refresh(student)
    return user, student


# ─── 1. Provider Factory ──────────────────────────────────────────────────────

async def test_factory_creates_mock_provider(engine, Session):
    """Factory should return MockLLMProvider when provider='mock'."""
    config = LLMConfig(provider="mock", model="mock-v1")
    provider = LLMProviderFactory.create(config)
    assert isinstance(provider, MockLLMProvider)
    assert provider.provider_name == "mock"
    print("[PASS] factory creates mock provider")


async def test_factory_unknown_provider_raises(engine, Session):
    """Factory should raise ValueError for unknown provider names."""
    raised = False
    try:
        LLMProviderFactory.create(LLMConfig(provider="unknown-llm"))
    except ValueError:
        raised = True
    assert raised
    print("[PASS] factory raises ValueError for unknown provider")


async def test_factory_lists_providers(engine, Session):
    """available_providers() should return all expected provider names."""
    providers = LLMProviderFactory.available_providers()
    assert "mock" in providers
    assert "openai" in providers
    assert "gemini" in providers
    assert "claude" in providers
    assert "groq" in providers
    assert "azure" in providers
    print(f"[PASS] available providers: {providers}")


# ─── 2. Mock Provider ─────────────────────────────────────────────────────────

async def test_mock_provider_chat(engine, Session):
    """MockLLMProvider.chat() should return a valid LLMResponse."""
    provider = MockLLMProvider(LLMConfig(provider="mock"))
    msgs = [ChatMessage(role="user", content="Tell me about my career")]
    response = await provider.chat(messages=msgs)
    assert response.content
    assert response.provider == "mock"
    assert response.total_tokens > 0
    assert response.finish_reason == "stop"
    print(f"[PASS] mock chat: {len(response.content)} chars, {response.total_tokens} tokens")


async def test_mock_provider_keyword_routing(engine, Session):
    """Mock provider should return project-specific response for project keywords."""
    provider = MockLLMProvider(LLMConfig(provider="mock"))
    msgs = [ChatMessage(role="user", content="What project should I build?")]
    resp = await provider.chat(messages=msgs)
    assert "project" in resp.content.lower()
    print("[PASS] mock provider routes project keywords correctly")


async def test_mock_provider_streaming(engine, Session):
    """stream() should yield multiple tokens."""
    provider = MockLLMProvider(LLMConfig(provider="mock"))
    msgs = [ChatMessage(role="user", content="Give me weekly plan")]
    tokens = []
    async for token in provider.stream(messages=msgs):
        tokens.append(token)
    full = "".join(tokens)
    assert len(tokens) > 5     # Multiple chunks
    assert len(full) > 50      # Substantial response
    print(f"[PASS] streaming: {len(tokens)} tokens, {len(full)} chars total")


async def test_mock_provider_is_available(engine, Session):
    """Mock provider is_available() should always return True."""
    provider = MockLLMProvider(LLMConfig(provider="mock"))
    assert await provider.is_available() is True
    print("[PASS] mock provider is_available=True")


async def test_mock_token_count(engine, Session):
    """count_tokens should return a positive integer."""
    provider = MockLLMProvider(LLMConfig(provider="mock"))
    count = await provider.count_tokens("Hello this is a test sentence with several words")
    assert count > 0
    print(f"[PASS] token count: {count}")


# ─── 3. Prompt Engine ─────────────────────────────────────────────────────────

async def test_prompt_engine_renders_template(engine, Session):
    """PromptEngine should render career_advisor template with student data."""
    pe = PromptEngine()
    rendered = pe.render(
        "career_advisor",
        student_name="Test Student", branch="AI & ML", branch_code="AIML",
        current_year=3, semester=5, target_role="ML Engineer",
        skills=[{"name": "Python", "score": 70, "proficiency_level": "INTERMEDIATE"}],
        completed_courses=5, total_courses=10,
        active_projects=1, certifications_earned=2,
        avg_readiness_score=62.5, top_company="Google India", top_company_score=62.5,
        goals=[{"goal_type": "TARGET_COMPANY", "goal_value": "Google India", "target_date": None, "status": "ACTIVE"}],
        user_query="What should I focus on this month?",
    )
    assert "Test Student" in rendered
    assert "ML Engineer" in rendered
    assert len(rendered) > 200
    print(f"[PASS] prompt engine rendered: {len(rendered)} chars")


async def test_prompt_engine_lists_templates(engine, Session):
    """list_templates() should return all 10 expected templates."""
    pe = PromptEngine()
    templates = pe.list_templates()
    expected = {"career_advisor", "roadmap_advisor", "project_recommender",
                "certification_recommender", "company_readiness", "skill_gap_analyzer",
                "resume_advisor", "interview_coach", "learning_planner", "weekly_planner"}
    assert expected.issubset(set(templates)), f"Missing templates: {expected - set(templates)}"
    print(f"[PASS] templates found: {sorted(templates)}")


async def test_prompt_engine_fallback(engine, Session):
    """PromptEngine should not raise on unknown template — uses fallback."""
    pe = PromptEngine()
    result = pe.render("non_existent_template", student_name="Student", user_query="test")
    assert isinstance(result, str)
    assert len(result) > 0
    print(f"[PASS] fallback rendered: {len(result)} chars")


# ─── 4. StudentContextAggregator ─────────────────────────────────────────────

async def test_aggregator_404_for_unknown_user(engine, Session):
    """Aggregator should raise NotFoundException for non-existent user."""
    async with Session() as db:
        from app.ai.context import StudentContextAggregator
        agg = StudentContextAggregator(db)
        raised = False
        try:
            await agg.load("non-existent-user-id")
        except NotFoundException:
            raised = True
        assert raised
        print("[PASS] aggregator raises 404 for unknown user")


async def test_aggregator_loads_context(engine, Session):
    """Aggregator should load a valid StudentContext for a real student."""
    async with Session() as db:
        from app.ai.context import StudentContextAggregator
        user, student = await _make_user_student(db, "agg.test@gitam.edu")
        agg = StudentContextAggregator(db)
        ctx = await agg.load(user.id)
        assert ctx.student_id == student.id
        assert ctx.student_name == "AI Test Student"
        assert ctx.branch_code == "AIML"
        assert ctx.semester == 5
        print(f"[PASS] aggregator loaded context: {ctx.student_name}, branch={ctx.branch_code}")


# ─── 5. Chat Service ─────────────────────────────────────────────────────────

async def test_chat_creates_conversation(engine, Session):
    """chat() should create a new Conversation and save 2 messages."""
    async with Session() as db:
        user, student = await _make_user_student(db, "chat.create@gitam.edu")
        service = AIMentorService(db)
        result = await service.chat(
            user_id=user.id,
            message="What should I focus on?",
            tool="career_advisor",
        )
        assert result["conversation_id"]
        assert result["response"]
        assert result["context_loaded"] is True
        assert result["provider"] == "mock"

        # Verify messages persisted
        msgs = await db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == result["conversation_id"])
        )
        msg_list = msgs.scalars().all()
        assert len(msg_list) == 2  # user + assistant
        roles = {m.role for m in msg_list}
        assert "user" in roles and "assistant" in roles
        print(f"[PASS] chat created conversation: {result['conversation_id'][:8]}...")


async def test_chat_caching(engine, Session):
    """Second identical call should return cached=True."""
    async with Session() as db:
        user, student = await _make_user_student(db, "chat.cache@gitam.edu")
        service = AIMentorService(db)
        msg = "Tell me about my career prospects"
        r1 = await service.chat(user_id=user.id, message=msg, tool="career_advisor")
        r2 = await service.chat(user_id=user.id, message=msg, tool="career_advisor",
                                conversation_id=r1["conversation_id"])
        assert r2["cached"] is True
        assert r1["response"] == r2["response"]
        print("[PASS] chat caching: second call cached=True")


async def test_conversation_history_persistence(engine, Session):
    """Multi-turn conversation should persist all messages in order."""
    async with Session() as db:
        user, student = await _make_user_student(db, "chat.multi@gitam.edu")
        service = AIMentorService(db)
        r1 = await service.chat(user_id=user.id, message="Hello AI mentor")
        r2 = await service.chat(user_id=user.id, message="Now tell me about projects",
                                conversation_id=r1["conversation_id"])
        r3 = await service.chat(user_id=user.id, message="Which certification next?",
                                conversation_id=r1["conversation_id"])

        msgs_res = await db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == r1["conversation_id"])
            .order_by(ConversationMessage.created_at)
        )
        msgs = msgs_res.scalars().all()
        assert len(msgs) == 6  # 3 user + 3 assistant
        assert msgs[0].role == "user"
        assert msgs[1].role == "assistant"
        print(f"[PASS] multi-turn conversation: {len(msgs)} messages persisted")


# ─── 6. Goals ─────────────────────────────────────────────────────────────────

async def test_set_goal_valid(engine, Session):
    """set_goal should create a StudentGoal record."""
    async with Session() as db:
        user, student = await _make_user_student(db, "goal.create@gitam.edu")
        service = AIMentorService(db)
        result = await service.set_goal(
            user_id=user.id,
            goal_type="TARGET_COMPANY",
            goal_value="Google India",
            target_date=date(2025, 12, 31),
        )
        assert result["id"]
        assert result["goal_type"] == "TARGET_COMPANY"
        assert result["goal_value"] == "Google India"
        assert result["status"] == "ACTIVE"

        goal_res = await db.execute(select(StudentGoal).where(StudentGoal.id == result["id"]))
        goal = goal_res.scalars().first()
        assert goal is not None
        print(f"[PASS] goal created: {goal.goal_type} = {goal.goal_value}")


async def test_set_goal_invalid_type(engine, Session):
    """set_goal with invalid goal_type should raise BadRequestException."""
    async with Session() as db:
        user, student = await _make_user_student(db, "goal.invalid@gitam.edu")
        service = AIMentorService(db)
        raised = False
        try:
            await service.set_goal(user_id=user.id, goal_type="INVALID_TYPE", goal_value="test")
        except BadRequestException:
            raised = True
        assert raised
        print("[PASS] invalid goal_type raises BadRequestException")


async def test_goal_status_update(engine, Session):
    """update_goal_status should transition ACTIVE -> ACHIEVED."""
    async with Session() as db:
        user, student = await _make_user_student(db, "goal.update@gitam.edu")
        service = AIMentorService(db)
        created = await service.set_goal(user_id=user.id, goal_type="TARGET_ROLE", goal_value="ML Engineer")
        result = await service.update_goal_status(user_id=user.id, goal_id=created["id"], status="ACHIEVED")
        assert result["status"] == "ACHIEVED"
        print(f"[PASS] goal status updated: ACTIVE -> ACHIEVED")


async def test_goal_ownership_enforced(engine, Session):
    """A different user should not be able to update another student's goal."""
    async with Session() as db:
        user1, _ = await _make_user_student(db, "goal.owner1@gitam.edu")
        user2, _ = await _make_user_student(db, "goal.owner2@gitam.edu")
        service = AIMentorService(db)
        created = await service.set_goal(user_id=user1.id, goal_type="RESEARCH", goal_value="IIT PhD")
        raised = False
        try:
            await service.update_goal_status(user_id=user2.id, goal_id=created["id"], status="DROPPED")
        except ForbiddenException:
            raised = True
        assert raised
        print("[PASS] goal ownership enforced: ForbiddenException for wrong user")


# ─── 7. Weekly Plan ───────────────────────────────────────────────────────────

async def test_weekly_plan_generation(engine, Session):
    """generate_weekly_plan should create a WeeklyPlan in the DB."""
    async with Session() as db:
        user, student = await _make_user_student(db, "plan.gen@gitam.edu")
        service = AIMentorService(db)
        result = await service.generate_weekly_plan(user_id=user.id)
        assert result["week_start"]
        assert isinstance(result["tasks"], list)
        assert result["estimated_hours"] >= 0

        plan_res = await db.execute(
            select(WeeklyPlan).where(WeeklyPlan.student_id == student.id)
        )
        plan = plan_res.scalars().first()
        assert plan is not None
        assert json.loads(plan.tasks_json)
        print(f"[PASS] weekly plan: {len(result['tasks'])} tasks, {result['estimated_hours']}h")


async def test_weekly_plan_caching(engine, Session):
    """Second call in same week should return cached=True plan."""
    async with Session() as db:
        user, student = await _make_user_student(db, "plan.cache@gitam.edu")
        service = AIMentorService(db)
        r1 = await service.generate_weekly_plan(user_id=user.id)
        r2 = await service.generate_weekly_plan(user_id=user.id)
        assert r2.get("cached") is True
        assert r1["week_start"] == r2["week_start"]
        print("[PASS] weekly plan cached on second call")


# ─── 8. Recommendations ───────────────────────────────────────────────────────

async def test_project_suggestions(engine, Session):
    """get_project_suggestions should return context + AI analysis."""
    async with Session() as db:
        user, _ = await _make_user_student(db, "proj.suggest@gitam.edu")
        service = AIMentorService(db)
        result = await service.get_project_suggestions(user_id=user.id)
        assert "recommended_projects" in result
        assert "ai_analysis" in result
        assert isinstance(result["recommended_projects"], list)
        print(f"[PASS] project suggestions: {len(result['recommended_projects'])} projects")


async def test_course_suggestions(engine, Session):
    """get_course_suggestions should include skill_gaps."""
    async with Session() as db:
        user, _ = await _make_user_student(db, "course.suggest@gitam.edu")
        service = AIMentorService(db)
        result = await service.get_course_suggestions(user_id=user.id)
        assert "recommended_courses" in result
        assert "skill_gaps" in result
        assert "ai_analysis" in result
        print(f"[PASS] course suggestions: {len(result['recommended_courses'])} courses, {len(result['skill_gaps'])} gaps")


async def test_company_readiness_response(engine, Session):
    """get_company_readiness should return readiness_scores list."""
    async with Session() as db:
        user, _ = await _make_user_student(db, "readiness.suggest@gitam.edu")
        service = AIMentorService(db)
        result = await service.get_company_readiness(user_id=user.id)
        assert "readiness_scores" in result
        assert "ai_analysis" in result
        assert isinstance(result["readiness_scores"], list)
        print(f"[PASS] company readiness: {len(result['readiness_scores'])} companies")


async def test_interview_prep_response(engine, Session):
    """get_interview_prep should return target_role + ai_prep_plan."""
    async with Session() as db:
        user, _ = await _make_user_student(db, "interview.suggest@gitam.edu")
        service = AIMentorService(db)
        result = await service.get_interview_prep(user_id=user.id)
        assert "target_role" in result
        assert "ai_prep_plan" in result
        assert result["target_role"] == "ML Engineer"
        print(f"[PASS] interview prep: target_role={result['target_role']}")


# ─── 9. Streaming ─────────────────────────────────────────────────────────────

async def test_streaming_yields_sse_events(engine, Session):
    """stream_chat should yield SSE-formatted events."""
    async with Session() as db:
        user, _ = await _make_user_student(db, "stream.test@gitam.edu")
        service = AIMentorService(db)
        events = []
        async for chunk in service.stream_chat(
            user_id=user.id,
            message="Tell me about my roadmap",
            tool="roadmap_advisor",
        ):
            events.append(chunk)
        assert len(events) > 2  # start + tokens + done
        # First event should be 'start'
        first = json.loads(events[0].replace("data: ", "").strip())
        assert first["type"] == "start"
        assert "conversation_id" in first
        # Last event should be 'done'
        last = json.loads(events[-1].replace("data: ", "").strip())
        assert last["type"] == "done"
        print(f"[PASS] streaming: {len(events)} SSE events, first={first['type']}, last={last['type']}")


# ─── 10. Delete Conversation ──────────────────────────────────────────────────

async def test_delete_conversation(engine, Session):
    """delete_conversation should remove from DB."""
    async with Session() as db:
        user, _ = await _make_user_student(db, "delete.convo@gitam.edu")
        service = AIMentorService(db)
        r = await service.chat(user_id=user.id, message="Hello, delete me")
        convo_id = r["conversation_id"]

        await service.delete_conversation(user_id=user.id, conversation_id=convo_id)

        res = await db.execute(select(Conversation).where(Conversation.id == convo_id))
        assert res.scalars().first() is None
        print(f"[PASS] conversation deleted: {convo_id[:8]}...")


# ─── 11. Provider Info ────────────────────────────────────────────────────────

async def test_provider_info(engine, Session):
    """get_provider_info should return correct provider details."""
    async with Session() as db:
        service = AIMentorService(db)
        info = await service.get_provider_info()
        assert info["provider"] == "mock"
        assert info["available"] is True
        assert len(info["templates"]) >= 8
        assert "mock" in info["available_providers"]
        print(f"[PASS] provider info: {info['provider']}, templates={len(info['templates'])}")


# ─── Runner ───────────────────────────────────────────────────────────────────

TESTS = [
    test_factory_creates_mock_provider,
    test_factory_unknown_provider_raises,
    test_factory_lists_providers,
    test_mock_provider_chat,
    test_mock_provider_keyword_routing,
    test_mock_provider_streaming,
    test_mock_provider_is_available,
    test_mock_token_count,
    test_prompt_engine_renders_template,
    test_prompt_engine_lists_templates,
    test_prompt_engine_fallback,
    test_aggregator_404_for_unknown_user,
    test_aggregator_loads_context,
    test_chat_creates_conversation,
    test_chat_caching,
    test_conversation_history_persistence,
    test_set_goal_valid,
    test_set_goal_invalid_type,
    test_goal_status_update,
    test_goal_ownership_enforced,
    test_weekly_plan_generation,
    test_weekly_plan_caching,
    test_project_suggestions,
    test_course_suggestions,
    test_company_readiness_response,
    test_interview_prep_response,
    test_streaming_yields_sse_events,
    test_delete_conversation,
    test_provider_info,
]

if __name__ == "__main__":
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
    for p in pathlib.Path(".").rglob("*.pyc"):
        p.unlink(missing_ok=True)

    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from app.database.base import Base

    async def run():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        passed = failed = 0
        for t in TESTS:
            try:
                await t(engine, Session)
                passed += 1
            except Exception as e:
                import traceback
                print(f"[FAIL] {t.__name__}: {e}")
                traceback.print_exc()
                failed += 1
        print()
        print("=" * 60)
        print(f"AI Mentor Engine: {passed} passed, {failed} failed")
        print("=" * 60)

    asyncio.run(run())
