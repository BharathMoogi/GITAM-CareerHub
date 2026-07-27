"""
Jinja2 Prompt Engine.

All AI prompts live in templates/  — never hardcoded in endpoints or services.
This ensures:
  - Prompts are versionable (tracked in git)
  - Non-engineers can tweak prompts without touching Python
  - A/B testing is trivial (swap template file, restart)
  - Jinja2 gives full conditional logic, loops, and filters

Usage:
    engine = PromptEngine()
    prompt = engine.render("career_advisor", student_context=ctx, user_query=query)
"""
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("app.ai.prompts.engine")

# Templates directory is alongside this file
TEMPLATES_DIR = Path(__file__).parent / "templates"


class PromptEngine:
    """
    Jinja2-based prompt rendering engine.

    Templates are .j2 files stored in app/ai/prompts/templates/.
    Each template receives a rich context dict with the student's full profile.
    """

    def __init__(self, templates_dir: Optional[Path] = None):
        try:
            from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
            self._env = Environment(
                loader=FileSystemLoader(str(templates_dir or TEMPLATES_DIR)),
                undefined=StrictUndefined,
                autoescape=select_autoescape(enabled_extensions=[]),
                trim_blocks=True,
                lstrip_blocks=True,
            )
            self._available = True
            logger.info(f"PromptEngine: Jinja2 loaded from {templates_dir or TEMPLATES_DIR}")
        except ImportError:
            logger.warning("Jinja2 not installed — PromptEngine using string fallback. Run: pip install jinja2")
            self._available = False

    def render(self, template_name: str, **context: Any) -> str:
        """
        Render a named prompt template with the given context.

        Args:
            template_name: Template filename without .j2 extension (e.g. "career_advisor")
            **context: Variables injected into the template

        Returns:
            Rendered prompt string ready to send to the LLM.
        """
        if not self._available:
            return self._fallback_render(template_name, **context)

        filename = f"{template_name}.j2"
        try:
            template = self._env.get_template(filename)
            return template.render(**context)
        except Exception as exc:
            logger.error(f"PromptEngine: Failed to render '{filename}': {exc}")
            return self._fallback_render(template_name, **context)

    def _fallback_render(self, template_name: str, **context: Any) -> str:
        """
        String-based fallback when Jinja2 is unavailable.
        Tries to load raw template file and do simple .format() substitution.
        """
        filename = TEMPLATES_DIR / f"{template_name}.j2"
        if filename.exists():
            try:
                raw = filename.read_text(encoding="utf-8")
                # Remove Jinja2 block tags and use raw content
                import re
                raw = re.sub(r"\{%-?.*?-?%\}", "", raw, flags=re.DOTALL)
                raw = re.sub(r"\{\{.*?\}\}", lambda m: str(context.get(m.group(0).strip("{ }").strip(), "")), raw)
                return raw.strip()
            except Exception:
                pass
        # Last resort
        student_name = context.get("student_name", "Student")
        return (
            f"You are an AI Career Mentor for GITAM University helping {student_name}. "
            f"Answer the student's question based on their academic profile."
        )

    def list_templates(self) -> list:
        """Return names of all available prompt templates."""
        if TEMPLATES_DIR.exists():
            return [f.stem for f in TEMPLATES_DIR.glob("*.j2")]
        return []
