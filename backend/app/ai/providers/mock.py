"""
Mock LLM Provider — for testing and development without API keys.

Returns deterministic, structured fake responses that exercise the full
request/response pipeline. The mock is the default provider when no
API key is configured.
"""
import json
from typing import AsyncIterator, Dict, List, Optional
from app.ai.providers.base import BaseLLMProvider, ChatMessage, LLMConfig, LLMResponse

_MOCK_RESPONSES: Dict[str, str] = {
    "career_advisor": (
        "Based on your academic profile and current skill set, here are my top recommendations:\n\n"
        "1. **Strengthen Core Skills**: Focus on Data Structures and Algorithms — essential for product company interviews.\n"
        "2. **Target Certifications**: The NPTEL 'Machine Learning' and Google's TensorFlow Developer Certificate align perfectly with your goals.\n"
        "3. **Project Priority**: Build a real-world AI project demonstrating end-to-end pipeline skills.\n"
        "4. **Company Readiness**: Your current readiness score suggests 6-8 weeks of focused preparation before applying.\n\n"
        "*This advice is based on your complete academic profile, completed courses, and industry data.*"
    ),
    "roadmap_advisor": (
        "Your roadmap progress shows excellent momentum. Here's what to focus on next:\n\n"
        "**Current Status**: Semester 5 modules largely complete.\n"
        "**Next Priority Modules**:\n"
        "- Deep Learning Fundamentals (estimated 20 hours)\n"
        "- MLOps & Model Deployment (estimated 15 hours)\n\n"
        "**Recommendation**: Complete the pending DSA module before moving to advanced topics."
    ),
    "project_recommender": (
        "Based on your skill profile and career goals, these projects will have the highest impact:\n\n"
        "1. **End-to-End ML Pipeline** — Demonstrates MLOps skills valued at Google & Amazon\n"
        "2. **Real-Time Object Detection** — Computer vision project relevant to NVIDIA & Qualcomm\n"
        "3. **Recommendation System** — Classic but impactful for data science roles\n\n"
        "All three projects are in your approved roadmap and aligned to your target companies."
    ),
    "skill_gap_analyzer": (
        "**Skill Gap Analysis vs Your Target Companies**\n\n"
        "| Skill | Required Level | Your Level | Gap |\n"
        "|-------|---------------|------------|-----|\n"
        "| Python | ADVANCED | INTERMEDIATE | Medium |\n"
        "| TensorFlow | INTERMEDIATE | BEGINNER | High |\n"
        "| System Design | INTERMEDIATE | BEGINNER | High |\n\n"
        "**Action Plan**: Prioritize TensorFlow certification and system design practice."
    ),
    "weekly_planner": (
        "**Your Personalized Weekly Plan**\n\n"
        "**Monday–Tuesday**: Complete DSA Module 3 (4 hrs/day)\n"
        "**Wednesday**: TensorFlow tutorial + hands-on practice (3 hrs)\n"
        "**Thursday**: Work on ML Pipeline project (4 hrs)\n"
        "**Friday**: Mock interview + Leetcode (2 hrs)\n"
        "**Weekend**: Review + project documentation\n\n"
        "**Estimated Total**: 22 hours | **Goal**: Advance readiness score by 5 points"
    ),
    "interview_coach": (
        "**Interview Preparation Plan for Your Target Companies**\n\n"
        "**Round 1 - Online Assessment**:\n"
        "- Practice 20 medium Leetcode problems in arrays, trees, DP\n"
        "- Time: 45 min/session, 5 sessions\n\n"
        "**Round 2 - Technical**:\n"
        "- System design: Start with 'Designing an ML Serving System'\n"
        "- ML concepts: Bias-variance tradeoff, regularization, model evaluation\n\n"
        "**Round 3 - HR**:\n"
        "- Prepare 3 STAR-format stories from your projects\n"
        "- Research company values and recent AI initiatives"
    ),
    "default": (
        "I've analyzed your complete academic profile — your courses, projects, skills, certifications, "
        "industry readiness scores, and applications. Based on this data, I'm here to provide "
        "personalized career guidance. What specific aspect would you like to explore?"
    ),
}


class MockLLMProvider(BaseLLMProvider):
    """
    Mock provider that returns structured, deterministic responses.
    Used for:
      - Local development without API keys
      - Unit and integration testing
      - CI/CD pipeline testing

    Responses are keyed by detecting keywords in the last user message.
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._call_count = 0

    @property
    def provider_name(self) -> str:
        return "mock"

    def _pick_response(self, messages: List[ChatMessage]) -> str:
        """Select an appropriate mock response based on message content."""
        last_user = next(
            (m.content.lower() for m in reversed(messages) if m.role == "user"),
            "",
        )
        if any(k in last_user for k in ["career", "goal", "advice", "guidance"]):
            return _MOCK_RESPONSES["career_advisor"]
        if any(k in last_user for k in ["roadmap", "module", "semester", "progress"]):
            return _MOCK_RESPONSES["roadmap_advisor"]
        if any(k in last_user for k in ["project", "build", "develop"]):
            return _MOCK_RESPONSES["project_recommender"]
        if any(k in last_user for k in ["skill", "gap", "missing", "learn"]):
            return _MOCK_RESPONSES["skill_gap_analyzer"]
        if any(k in last_user for k in ["week", "plan", "schedule", "daily"]):
            return _MOCK_RESPONSES["weekly_planner"]
        if any(k in last_user for k in ["interview", "prepare", "round", "question"]):
            return _MOCK_RESPONSES["interview_coach"]
        return _MOCK_RESPONSES["default"]

    async def chat(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> LLMResponse:
        self._call_count += 1
        content = self._pick_response(messages)
        # Simulate token usage
        total_tokens = len(content.split()) * 2
        return LLMResponse(
            content=content,
            model="mock-v1",
            provider="mock",
            prompt_tokens=total_tokens // 3,
            completion_tokens=total_tokens * 2 // 3,
            total_tokens=total_tokens,
            finish_reason="stop",
        )

    async def stream(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        content = self._pick_response(messages)
        # Stream word by word to simulate real streaming
        words = content.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")

    async def count_tokens(self, text: str) -> int:
        # Rough approximation: 4 chars ≈ 1 token
        return max(1, len(text) // 4)

    async def is_available(self) -> bool:
        return True

    @property
    def call_count(self) -> int:
        return self._call_count
