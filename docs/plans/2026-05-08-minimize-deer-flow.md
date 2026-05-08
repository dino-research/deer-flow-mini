# Deer-Flow Mini — Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Minimize Deer-Flow into a lean version for internal deployment with Gemma 4 E4B (32K context).

**Architecture:** Docker Compose stack with Frontend + Gateway + SearXNG + AIO Sandbox. OpenAI-compatible LLM only.

**Tech Stack:** Python 3.12, LangGraph, FastAPI, Next.js, SearXNG, httpx+readabilipy

**Design doc:** `docs/plans/2026-05-08-minimize-deer-flow-design.md`

---

### Task 1: Delete IM Channels

**Files:**
- Delete: `backend/app/channels/` (entire directory except `__init__.py`)
- Delete: `backend/tests/test_discord_channel.py`
- Delete: `backend/tests/test_feishu_parser.py`
- Delete: `backend/tests/test_wechat_channel.py`
- Delete: `backend/tests/test_dingtalk_channel.py`
- Modify: `backend/app/channels/__init__.py` → empty file

**Step 1:** Delete all channel implementation files and their tests.

```bash
cd backend/app/channels && ls -la  # verify files
```

```bash
rm -f backend/app/channels/dingtalk.py backend/app/channels/discord.py \
  backend/app/channels/feishu.py backend/app/channels/slack.py \
  backend/app/channels/telegram.py backend/app/channels/wechat.py \
  backend/app/channels/wecom.py backend/app/channels/manager.py \
  backend/app/channels/message_bus.py backend/app/channels/service.py \
  backend/app/channels/store.py backend/app/channels/base.py \
  backend/app/channels/commands.py
```

**Step 2:** Delete channel test files.

```bash
rm -f backend/tests/test_discord_channel.py backend/tests/test_feishu_parser.py \
  backend/tests/test_wechat_channel.py backend/tests/test_dingtalk_channel.py
```

**Step 3:** Empty the `__init__.py` stub.

```python
# backend/app/channels/__init__.py
```

**Step 4:** Search and remove any remaining channel imports in gateway routers.

```bash
grep -rn "channels" backend/app/gateway/ --include="*.py"
```

Fix any dangling imports found.

**Step 5:** Commit.

```bash
git add -A && git commit -m "chore: remove all IM channel integrations"
```

---

### Task 2: Delete Unused Model Providers

**Files:**
- Delete: `deerflow/models/claude_provider.py`
- Delete: `deerflow/models/openai_codex_provider.py`
- Delete: `deerflow/models/patched_deepseek.py`
- Delete: `deerflow/models/patched_minimax.py`
- Delete: `deerflow/models/vllm_provider.py`
- Delete: `deerflow/models/mindie_provider.py`
- Modify: `deerflow/models/factory.py` — remove Codex/MindIE refs (lines 120-139)

**Step 1:** Delete provider files.

```bash
cd backend/packages/harness
rm -f deerflow/models/claude_provider.py deerflow/models/openai_codex_provider.py \
  deerflow/models/patched_deepseek.py deerflow/models/patched_minimax.py \
  deerflow/models/vllm_provider.py deerflow/models/mindie_provider.py
```

**Step 2:** Edit `factory.py` — remove the Codex import (line 120-133) and MindIE block (lines 135-139). Replace with pass-through.

Remove these blocks from `create_chat_model()`:
```python
# DELETE: lines 119-133 (Codex Responses API)
from deerflow.models.openai_codex_provider import CodexChatModel
if issubclass(model_class, CodexChatModel):
    # ... entire block ...

# DELETE: lines 135-139 (MindIE)
if getattr(model_class, "__name__", "") == "MindIEChatModel":
    model_settings_from_config["max_retries"] = ...
```

**Step 3:** Commit.

```bash
git add -A && git commit -m "chore: remove unused model providers (claude, codex, deepseek, minimax, vllm, mindie)"
```

---

### Task 3: Remove Tracing (LangSmith/Langfuse)

**Files:**
- Modify: `deerflow/tracing/factory.py` — return empty list always
- Modify: `deerflow/tracing/__init__.py`
- Modify: `deerflow/config/__init__.py` — remove tracing exports
- Modify: `deerflow/config/tracing_config.py` — gut or delete
- Delete: `backend/tests/test_tracing_factory.py`
- Delete: `backend/tests/test_tracing_config.py`
- Modify: `deerflow/models/factory.py` — remove tracing callback attachment

**Step 1:** Replace `deerflow/tracing/factory.py` with stub:

```python
from __future__ import annotations
from typing import Any

def build_tracing_callbacks() -> list[Any]:
    """Tracing disabled in deer-flow-mini."""
    return []
```

**Step 2:** Simplify `deerflow/config/__init__.py` — remove all tracing imports.

**Step 3:** In `deerflow/models/factory.py`, remove line 8 (`from deerflow.tracing import build_tracing_callbacks`) and lines 152-156 (callback attachment). Keep the import as a no-op or remove entirely.

**Step 4:** Delete test files and commit.

```bash
rm -f backend/tests/test_tracing_factory.py backend/tests/test_tracing_config.py
git add -A && git commit -m "chore: remove langsmith/langfuse tracing"
```

---

### Task 4: Delete Unused Community Tools

**Files:**
- Delete: `deerflow/community/exa/`
- Delete: `deerflow/community/firecrawl/`
- Delete: `deerflow/community/infoquest/`
- Delete: `deerflow/community/jina_ai/`
- Delete: `deerflow/community/serper/`
- Delete: `deerflow/community/tavily/`
- Delete: `deerflow/community/image_search/`
- Delete: `deerflow/community/ddg_search/`

**Step 1:** Delete all unused community tool directories.

```bash
cd backend/packages/harness
rm -rf deerflow/community/exa deerflow/community/firecrawl \
  deerflow/community/infoquest deerflow/community/jina_ai \
  deerflow/community/serper deerflow/community/tavily \
  deerflow/community/image_search deerflow/community/ddg_search
```

**Step 2:** Verify `deerflow/community/aio_sandbox/` still exists.

**Step 3:** Commit.

```bash
git add -A && git commit -m "chore: remove unused community tools (exa, firecrawl, infoquest, jina, serper, tavily, ddg, image_search)"
```

---

### Task 5: Remove ACP, Guardrails, Tool Search, Skill Evolution

**Files:**
- Delete: `deerflow/config/acp_config.py`
- Delete: `deerflow/tools/builtins/invoke_acp_agent_tool.py`
- Delete: `deerflow/tools/builtins/tool_search.py`
- Delete: `deerflow/tools/builtins/view_image_tool.py`
- Delete: `deerflow/tools/skill_manage_tool.py`
- Delete: `deerflow/guardrails/` (entire directory)
- Delete: `deerflow/config/guardrails_config.py`
- Delete: `deerflow/config/tool_search_config.py`
- Delete: `deerflow/config/skill_evolution_config.py`
- Delete: `deerflow/agents/middlewares/deferred_tool_filter_middleware.py`
- Modify: `deerflow/config/app_config.py` — remove ACP, guardrails, tool_search, skill_evolution imports
- Modify: `deerflow/config/__init__.py` — remove SkillEvolutionConfig, ExtensionsConfig
- Modify: `deerflow/tools/tools.py` — remove ACP and tool_search blocks
- Modify: `deerflow/agents/lead_agent/agent.py` — remove deferred tool middleware (lines 289-293)
- Modify: `deerflow/agents/middlewares/tool_error_handling_middleware.py` — remove guardrail import (line 104)

**Step 1:** Delete files listed above.

**Step 2:** Edit `deerflow/config/app_config.py`:
- Remove import of `acp_config`, `guardrails_config`, `tool_search_config`, `skill_evolution_config`
- Remove corresponding fields from `AppConfig` class
- Remove `load_*_from_dict()` calls in the loader function

**Step 3:** Edit `deerflow/tools/tools.py`:
- Remove ACP tool block (lines ~141-154)
- Remove tool_search/deferred registry blocks (lines ~124-140)
- Remove `from deerflow.tools.builtins.tool_search import reset_deferred_registry` (line 10)

**Step 4:** Edit `deerflow/agents/lead_agent/agent.py`:
- Remove deferred tool filter middleware block (lines 289-293)

**Step 5:** Edit `deerflow/agents/middlewares/tool_error_handling_middleware.py`:
- Remove guardrail import at line 104

**Step 6:** Commit.

```bash
git add -A && git commit -m "chore: remove ACP, guardrails, tool_search, skill_evolution, view_image"
```

---

### Task 6: Clean Dependencies

**Files:**
- Modify: `backend/packages/harness/pyproject.toml`

**Step 1:** Remove these from `dependencies`:

```
agent-client-protocol, exa-py, kubernetes, langchain-anthropic,
langchain-deepseek, langfuse, tavily-python, firecrawl-py,
ddgs, langchain-google-genai
```

**Step 2:** Run `uv sync` to verify resolution works.

**Step 3:** Commit.

```bash
git add -A && git commit -m "chore: remove unused Python dependencies"
```

---

### Task 7: Build SearXNG Community Tool

**Files:**
- Create: `deerflow/community/searxng/__init__.py`
- Create: `deerflow/community/searxng/tools.py`

**Step 1:** Create `__init__.py`:

```python
from .tools import web_search_tool
__all__ = ["web_search_tool"]
```

**Step 2:** Create `tools.py`:

```python
"""SearXNG web search tool for deer-flow-mini."""
import os
import logging
import httpx
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

SEARXNG_BASE_URL = os.getenv("SEARXNG_BASE_URL", "http://searxng:8080")

@tool
def web_search_tool(query: str, max_results: int = 5) -> str:
    """Search the web using SearXNG. Returns titles, URLs, and snippets."""
    params = {"q": query, "format": "json", "count": max_results}
    try:
        resp = httpx.get(f"{SEARXNG_BASE_URL}/search", params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])[:max_results]
        if not results:
            return "No results found."
        output = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "No title")
            url = r.get("url", "")
            snippet = r.get("content", "")[:200]
            output.append(f"{i}. [{title}]({url})\n   {snippet}")
        return "\n\n".join(output)
    except Exception as e:
        logger.error(f"SearXNG search failed: {e}")
        return f"Search failed: {e}"
```

**Step 3:** Register in tool config. Find where tools are assembled (likely `config.example.yaml` tool_groups) and add searxng entry.

**Step 4:** Commit.

```bash
git add -A && git commit -m "feat: add SearXNG community tool"
```

---

### Task 8: Build Local Web Fetch Tool

**Files:**
- Create: `deerflow/community/local_fetch/__init__.py`
- Create: `deerflow/community/local_fetch/tools.py`

**Step 1:** Create `__init__.py`:

```python
from .tools import web_fetch_tool
__all__ = ["web_fetch_tool"]
```

**Step 2:** Create `tools.py`:

```python
"""Local web page fetcher using httpx + readabilipy."""
import logging
import httpx
from langchain_core.tools import tool
from markdownify import markdownify as md

logger = logging.getLogger(__name__)

@tool
def web_fetch_tool(url: str) -> str:
    """Fetch a web page and return its content as Markdown."""
    try:
        resp = httpx.get(url, timeout=20, follow_redirects=True,
                         headers={"User-Agent": "DeerFlow-Mini/1.0"})
        resp.raise_for_status()
        from readabilipy import simple_json_from_html_string
        article = simple_json_from_html_string(resp.text, use_readability=True)
        content = article.get("plain_content") or article.get("content", "")
        if content:
            result = md(content, strip=["img", "script", "style"])
        else:
            result = md(resp.text, strip=["img", "script", "style"])
        return result[:16000]  # Limit for 32K context model
    except Exception as e:
        logger.error(f"Web fetch failed for {url}: {e}")
        return f"Failed to fetch {url}: {e}"
```

**Step 3:** Commit.

```bash
git add -A && git commit -m "feat: add local web fetch tool (httpx + readabilipy)"
```

---

### Task 9: Delete Skills (13 total)

**Files:**
- Delete 13 skill directories from `skills/public/`

**Step 1:** Delete skills.

```bash
rm -rf skills/public/claude-to-deerflow skills/public/find-skills \
  skills/public/image-generation skills/public/podcast-generation \
  skills/public/ppt-generation skills/public/vercel-deploy-claimable \
  skills/public/video-generation skills/public/newsletter-generation \
  skills/public/frontend-design skills/public/web-design-guidelines \
  skills/public/bootstrap skills/public/skill-creator skills/public/surprise-me
```

**Step 2:** Verify 7 skills remain: `ls skills/public/`

Expected: deep-research, data-analysis, chart-visualization, code-documentation, consulting-analysis, github-deep-research, systematic-literature-review

**Step 3:** Commit.

```bash
git add -A && git commit -m "chore: remove 13 unused skills, keep 7 core skills"
```

---

### Task 10: Optimize System Prompt for 32K Context

**Files:**
- Modify: `deerflow/agents/lead_agent/prompt.py`

This is the highest-impact task. Target: reduce from ~829 lines to ~300 lines.

**Step 1:** Remove `_build_acp_section()` function entirely.

**Step 2:** Remove `get_deferred_tools_prompt_section()` function entirely.

**Step 3:** Remove `_build_skill_evolution_section()` function entirely.

**Step 4:** Compress `_build_subagent_section()`:
- Remove verbose 3-example block, keep 1 concise example
- Remove counter-examples
- Remove multi-batch explanation
- Target: ~80 lines instead of ~362

**Step 5:** Compress clarification section: remove 5 scenario examples, keep core rules only (~30 lines).

**Step 6:** Compress citations section: remove formatting examples (~20 lines).

**Step 7:** Remove `{deferred_tools_section}` from the main template string.

**Step 8:** Remove `{acp_section}` from the main template string.

**Step 9:** Update `build_system_prompt()` to not call removed functions.

**Step 10:** Commit.

```bash
git add -A && git commit -m "perf: compress system prompt from ~10K to ~2.5K tokens for 32K context"
```

---

### Task 11: Update Config Defaults for 32K Context

**Files:**
- Modify: `config.example.yaml`

**Step 1:** Simplify config to ~200 lines. Key changes:

```yaml
summarization:
  trigger: [{type: tokens, value: 8000}]
  keep: {type: messages, value: 6}
  trim_tokens_to_summarize: 8000

memory:
  max_injection_tokens: 500
  max_facts: 30

sandbox:
  bash_output_max_chars: 8000
  read_file_output_max_chars: 16000
  ls_output_max_chars: 8000
```

**Step 2:** Remove all channel configs, tracing configs, guardrails configs, unused provider examples.

**Step 3:** Add SearXNG tool group config.

**Step 4:** Commit.

```bash
git add -A && git commit -m "chore: simplify config.example.yaml for 32K context"
```

---

### Task 12: Frontend Cleanup

**Files:**
- Delete: `frontend/src/app/blog/` (if exists)
- Delete: `frontend/src/core/blog/` (if exists)
- Delete: `frontend/src/app/mock/` (if exists)
- Delete: `frontend/public/demo/`

**Step 1:** Delete blog, mock, and demo directories.

**Step 2:** Remove references in frontend routing if needed.

**Step 3:** Commit.

```bash
git add -A && git commit -m "chore: remove blog, mock, and demo data from frontend"
```

---

### Task 13: Documentation & Docker Compose

**Files:**
- Delete: `README_fr.md`, `README_ja.md`, `README_ru.md`, `README_zh.md`
- Delete: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`
- Modify: `docker-compose.yaml` — add SearXNG service
- Create: `searxng/settings.yml` — SearXNG config
- Modify: `.env.example` — strip to essentials, add `SEARXNG_BASE_URL`

**Step 1:** Delete unnecessary docs.

**Step 2:** Update docker-compose to include SearXNG service.

**Step 3:** Create minimal SearXNG settings file.

**Step 4:** Update `.env.example`.

**Step 5:** Commit.

```bash
git add -A && git commit -m "chore: simplify docs, add SearXNG to docker-compose"
```

---

### Task 14: Verification

**Step 1:** Run `uv sync` — verify deps install.

**Step 2:** Run `uv run pytest` (remaining tests) — verify no import errors.

**Step 3:** Run `docker compose build` — verify builds.

**Step 4:** Run `docker compose up` — verify services start.

**Step 5:** Test chat with OpenAI-compatible endpoint.

**Step 6:** Test SearXNG search.

**Step 7:** Test local web fetch.

**Step 8:** Measure system prompt token count (target: <3K tokens).
