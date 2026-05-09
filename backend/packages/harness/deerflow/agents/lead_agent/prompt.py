from __future__ import annotations

import asyncio
import logging
import threading
from datetime import datetime
from functools import lru_cache
from typing import TYPE_CHECKING

from deerflow.config.agents_config import load_agent_soul
from deerflow.skills.storage import get_or_new_skill_storage
from deerflow.skills.types import Skill, SkillCategory
from deerflow.subagents import get_available_subagent_names

if TYPE_CHECKING:
    from deerflow.config.app_config import AppConfig

logger = logging.getLogger(__name__)

_ENABLED_SKILLS_REFRESH_WAIT_TIMEOUT_SECONDS = 5.0
_enabled_skills_lock = threading.Lock()
_enabled_skills_cache: list[Skill] | None = None
_enabled_skills_by_config_cache: dict[int, tuple[object, list[Skill]]] = {}
_enabled_skills_refresh_active = False
_enabled_skills_refresh_version = 0
_enabled_skills_refresh_event = threading.Event()


def _load_enabled_skills_sync() -> list[Skill]:
    return list(get_or_new_skill_storage().load_skills(enabled_only=True))


def _start_enabled_skills_refresh_thread() -> None:
    threading.Thread(
        target=_refresh_enabled_skills_cache_worker,
        name="deerflow-enabled-skills-loader",
        daemon=True,
    ).start()


def _refresh_enabled_skills_cache_worker() -> None:
    global _enabled_skills_cache, _enabled_skills_refresh_active

    while True:
        with _enabled_skills_lock:
            target_version = _enabled_skills_refresh_version

        try:
            skills = _load_enabled_skills_sync()
        except Exception:
            logger.exception("Failed to load enabled skills for prompt injection")
            skills = []

        with _enabled_skills_lock:
            if _enabled_skills_refresh_version == target_version:
                _enabled_skills_cache = skills
                _enabled_skills_refresh_active = False
                _enabled_skills_refresh_event.set()
                return

            _enabled_skills_cache = None


def _ensure_enabled_skills_cache() -> threading.Event:
    global _enabled_skills_refresh_active

    with _enabled_skills_lock:
        if _enabled_skills_cache is not None:
            _enabled_skills_refresh_event.set()
            return _enabled_skills_refresh_event
        if _enabled_skills_refresh_active:
            return _enabled_skills_refresh_event
        _enabled_skills_refresh_active = True
        _enabled_skills_refresh_event.clear()

    _start_enabled_skills_refresh_thread()
    return _enabled_skills_refresh_event


def _invalidate_enabled_skills_cache() -> threading.Event:
    global _enabled_skills_cache, _enabled_skills_refresh_active, _enabled_skills_refresh_version

    _get_cached_skills_prompt_section.cache_clear()
    with _enabled_skills_lock:
        _enabled_skills_cache = None
        _enabled_skills_by_config_cache.clear()
        _enabled_skills_refresh_version += 1
        _enabled_skills_refresh_event.clear()
        if _enabled_skills_refresh_active:
            return _enabled_skills_refresh_event
        _enabled_skills_refresh_active = True

    _start_enabled_skills_refresh_thread()
    return _enabled_skills_refresh_event


def prime_enabled_skills_cache() -> None:
    _ensure_enabled_skills_cache()


def warm_enabled_skills_cache(timeout_seconds: float = _ENABLED_SKILLS_REFRESH_WAIT_TIMEOUT_SECONDS) -> bool:
    if _ensure_enabled_skills_cache().wait(timeout=timeout_seconds):
        return True

    logger.warning("Timed out waiting %.1fs for enabled skills cache warm-up", timeout_seconds)
    return False


def _get_enabled_skills():
    return get_cached_enabled_skills()


def get_cached_enabled_skills() -> list[Skill]:
    """Return the cached enabled-skills list, kicking off a background refresh on miss."""
    with _enabled_skills_lock:
        cached = _enabled_skills_cache

    if cached is not None:
        return list(cached)

    _ensure_enabled_skills_cache()
    return []


def get_enabled_skills_for_config(app_config: AppConfig | None = None) -> list[Skill]:
    """Return enabled skills using the caller's config source."""
    if app_config is None:
        return _get_enabled_skills()

    cache_key = id(app_config)
    with _enabled_skills_lock:
        cached = _enabled_skills_by_config_cache.get(cache_key)
        if cached is not None:
            cached_config, cached_skills = cached
            if cached_config is app_config:
                return list(cached_skills)

    skills = list(get_or_new_skill_storage(app_config=app_config).load_skills(enabled_only=True))
    with _enabled_skills_lock:
        _enabled_skills_by_config_cache[cache_key] = (app_config, skills)
    return list(skills)


def _skill_mutability_label(category: SkillCategory | str) -> str:
    return "[custom, editable]" if category == SkillCategory.CUSTOM else "[built-in]"


def clear_skills_system_prompt_cache() -> None:
    _invalidate_enabled_skills_cache()


async def refresh_skills_system_prompt_cache_async() -> None:
    await asyncio.to_thread(_invalidate_enabled_skills_cache().wait)


def _build_available_subagents_description(available_names: list[str], bash_available: bool, *, app_config: AppConfig | None = None) -> str:
    """Dynamically build subagent type descriptions from registry."""
    builtin_descriptions = {
        "general-purpose": "For ANY non-trivial task - web research, code exploration, file operations, analysis, etc.",
        "bash": ("For command execution (git, build, test, deploy operations)" if bash_available else "Not available in the current sandbox configuration."),
    }

    from deerflow.subagents.registry import get_subagent_config

    lines = []
    for name in available_names:
        if name in builtin_descriptions:
            lines.append(f"- **{name}**: {builtin_descriptions[name]}")
        else:
            config = get_subagent_config(name, app_config=app_config)
            if config is not None:
                desc = config.description.split("\n")[0].strip()
                lines.append(f"- **{name}**: {desc}")

    return "\n".join(lines)


def _build_subagent_section(max_concurrent: int, *, app_config: AppConfig | None = None) -> str:
    """Build a compact subagent system prompt section."""
    n = max_concurrent
    available_names = get_available_subagent_names(app_config=app_config) if app_config is not None else get_available_subagent_names()
    bash_available = "bash" in available_names
    available_subagents = _build_available_subagents_description(available_names, bash_available, app_config=app_config)

    return f"""<subagent_system>
**SUBAGENT MODE ACTIVE — DECOMPOSE, DELEGATE, SYNTHESIZE**

You are a task orchestrator. Break complex tasks into parallel sub-tasks using the `task` tool.

**HARD LIMIT: max {n} `task` calls per response.** Excess calls are silently discarded.
- Count sub-tasks in thinking. If count > {n}, batch across turns.
- Only use `task` when 2+ sub-tasks can run in parallel.
- Single tasks → execute directly, don't wrap in subagents.

**Available Subagents:**
{available_subagents}

**Example:** "Why is X stock declining?" → 3 parallel subagents (financials, news, market trends) → synthesize.

**Workflow:** COUNT sub-tasks → BATCH (≤{n}/turn) → EXECUTE → SYNTHESIZE after all batches.
The task tool runs subagents asynchronously; the backend polls for completion automatically.
</subagent_system>"""


SYSTEM_PROMPT_TEMPLATE = """
<role>
You are {agent_name}, an AI assistant optimized for research and analysis tasks.
</role>

{soul}
{self_update_section}
{memory_context}

<thinking_style>
- Think concisely about the user's request BEFORE acting
- If anything is unclear or missing, ask for clarification FIRST
{subagent_thinking}- Never write your full answer in thinking; outline only
- After thinking, you MUST provide a visible response
</thinking_style>

<clarification_system>
**WORKFLOW: CLARIFY → PLAN → ACT**
If required details are missing or ambiguous, call `ask_clarification` IMMEDIATELY before starting work.

Scenarios requiring clarification:
- Missing information (e.g. unspecified target, environment)
- Ambiguous requirements (multiple valid interpretations)
- Approach choices (multiple valid methods)
- Risky/destructive operations (need confirmation)

Rules: Never assume. Never start work then clarify mid-execution. Always clarify FIRST.
</clarification_system>

{skills_section}

{subagent_section}

<working_directory existed="true">
- User uploads: `/mnt/user-data/uploads`
- User workspace: `/mnt/user-data/workspace` (default working directory)
- Output files: `/mnt/user-data/outputs` (final deliverables go here)

Uploaded files are listed in <uploaded_files> before each request. Use `read_file` to read them.
For PDF/PPT/Excel/Word files, converted Markdown versions (*.md) are available.
Prefer relative paths in scripts. Present final files using `present_files` tool.
{custom_mounts_section}
</working_directory>

<response_style>
- Clear and Concise: Avoid over-formatting unless requested
- Natural Tone: Use paragraphs and prose, not bullet points by default
- Action-Oriented: Focus on delivering results
</response_style>

<citations>
When using web search results, include inline citations: `[citation:Title](URL)` after claims.
Collect all references in a "Sources" section at the end of reports.
Sources section format: `[Title](URL) - Description` (standard markdown links, NOT citation: prefix).
</citations>

<critical_reminders>
- Clarification First: Always clarify unclear requirements BEFORE starting work
{subagent_reminder}- Skill First: Load relevant skill before complex tasks
- Output Files: Final deliverables must be in `/mnt/user-data/outputs`
- HTML Artifacts: When generating HTML files, create **self-contained** files with ALL JavaScript and CSS inline. Do NOT use separate .js or .css files. External CDN links are OK.
- Visual Output: Use `![desc](path)` for images and ```mermaid for diagrams. For data visualization, prefer the chart-visualization skill over raw HTML.
- Multi-tool: Utilize parallel tool calling for better performance
- Language Consistency: Match the user's language
- Always Respond: Thinking is internal; always provide a visible response
</critical_reminders>
"""


def _get_memory_context(agent_name: str | None = None, *, app_config: AppConfig | None = None) -> str:
    """Get memory context for injection into system prompt."""
    try:
        from deerflow.agents.memory import format_memory_for_injection, get_memory_data
        from deerflow.runtime.user_context import get_effective_user_id

        if app_config is None:
            from deerflow.config.memory_config import get_memory_config

            config = get_memory_config()
        else:
            config = app_config.memory

        if not config.enabled or not config.injection_enabled:
            return ""

        memory_data = get_memory_data(agent_name, user_id=get_effective_user_id())
        memory_content = format_memory_for_injection(memory_data, max_tokens=config.max_injection_tokens)

        if not memory_content.strip():
            return ""

        return f"""<memory>
{memory_content}
</memory>
"""
    except Exception:
        logger.exception("Failed to load memory context")
        return ""


@lru_cache(maxsize=32)
def _get_cached_skills_prompt_section(
    skill_signature: tuple[tuple[str, str, str, str], ...],
    available_skills_key: tuple[str, ...] | None,
    container_base_path: str,
) -> str:
    filtered = [(name, description, category, location) for name, description, category, location in skill_signature if available_skills_key is None or name in available_skills_key]
    skills_list = ""
    if filtered:
        skill_items = "\n".join(
            f"    <skill>\n        <name>{name}</name>\n        <description>{description} {_skill_mutability_label(category)}</description>\n        <location>{location}</location>\n    </skill>"
            for name, description, category, location in filtered
        )
        skills_list = f"<available_skills>\n{skill_items}\n</available_skills>"
    return f"""<skill_system>
You have access to skills that provide optimized workflows for specific tasks.

**Progressive Loading:** When a query matches a skill, call `read_file` on its main file, follow instructions, and load referenced resources as needed.

**Skills are located at:** {container_base_path}

{skills_list}

</skill_system>"""


def get_skills_prompt_section(available_skills: set[str] | None = None, *, app_config: AppConfig | None = None) -> str:
    """Generate the skills prompt section with available skills list."""
    skills = get_enabled_skills_for_config(app_config)

    if app_config is None:
        try:
            from deerflow.config import get_app_config

            config = get_app_config()
            container_base_path = config.skills.container_path
        except Exception:
            container_base_path = "/mnt/skills"
    else:
        config = app_config
        container_base_path = config.skills.container_path

    if not skills:
        return ""

    if available_skills is not None and not any(skill.name in available_skills for skill in skills):
        return ""

    skill_signature = tuple((skill.name, skill.description, skill.category, skill.get_container_file_path(container_base_path)) for skill in skills)
    available_key = tuple(sorted(available_skills)) if available_skills is not None else None
    if not skill_signature and available_key is not None:
        return ""
    return _get_cached_skills_prompt_section(skill_signature, available_key, container_base_path)


def get_agent_soul(agent_name: str | None) -> str:
    # Append SOUL.md (agent personality) if present
    soul = load_agent_soul(agent_name)
    if soul:
        return f"<soul>\n{soul}\n</soul>\n" if soul else ""
    return ""


def _build_self_update_section(agent_name: str | None) -> str:
    """Prompt block that teaches the custom agent to persist self-updates via update_agent."""
    if not agent_name:
        return ""
    return f"""<self_update>
You are running as custom agent **{agent_name}** with persisted SOUL.md and config.yaml.
To update your description, personality, skills, or model, use the `update_agent` tool.
Always pass the FULL replacement text for `soul`. Only pass fields that should change.
</self_update>
"""


def _build_custom_mounts_section(*, app_config: AppConfig | None = None) -> str:
    """Build a prompt section for explicitly configured sandbox mounts."""
    if app_config is None:
        try:
            from deerflow.config import get_app_config

            config = get_app_config()
        except Exception:
            logger.exception("Failed to load configured sandbox mounts for the lead-agent prompt")
            return ""
    else:
        config = app_config

    mounts = config.sandbox.mounts or []

    if not mounts:
        return ""

    lines = []
    for mount in mounts:
        access = "read-only" if mount.read_only else "read-write"
        lines.append(f"- Custom mount: `{mount.container_path}` ({access})")

    mounts_list = "\n".join(lines)
    return f"\n**Custom Mounted Directories:**\n{mounts_list}"


def apply_prompt_template(
    subagent_enabled: bool = False,
    max_concurrent_subagents: int = 3,
    *,
    agent_name: str | None = None,
    available_skills: set[str] | None = None,
    app_config: AppConfig | None = None,
) -> str:
    # Get memory context
    memory_context = _get_memory_context(agent_name, app_config=app_config)

    # Include subagent section only if enabled (from runtime parameter)
    n = max_concurrent_subagents
    subagent_section = _build_subagent_section(n, app_config=app_config) if subagent_enabled else ""

    # Add subagent reminder to critical_reminders if enabled
    subagent_reminder = f"- **Orchestrator Mode**: Decompose complex tasks into parallel sub-tasks. Max {n} `task` calls per response.\n" if subagent_enabled else ""

    # Add subagent thinking guidance if enabled
    subagent_thinking = f"- **DECOMPOSITION CHECK**: Can this be broken into 2+ parallel sub-tasks? If count > {n}, batch across turns.\n" if subagent_enabled else ""

    # Get skills section
    skills_section = get_skills_prompt_section(available_skills, app_config=app_config)

    # Build custom mounts section
    custom_mounts_section = _build_custom_mounts_section(app_config=app_config)

    # Format the prompt with dynamic skills and memory
    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        agent_name=agent_name or "DeerFlow Mini",
        soul=get_agent_soul(agent_name),
        self_update_section=_build_self_update_section(agent_name),
        skills_section=skills_section,
        memory_context=memory_context,
        subagent_section=subagent_section,
        subagent_reminder=subagent_reminder,
        subagent_thinking=subagent_thinking,
        custom_mounts_section=custom_mounts_section,
    )

    return prompt + f"\n<current_date>{datetime.now().strftime('%Y-%m-%d, %A')}</current_date>"
