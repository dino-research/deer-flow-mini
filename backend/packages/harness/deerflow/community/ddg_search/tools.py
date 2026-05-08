"""Web search tool with SearXNG primary + DuckDuckGo fallback.

Strategy:
  - Production (Docker): SearXNG available → use it, DDG as fallback
  - Development (native): SearXNG unavailable → auto-fallback to DDG
"""

import logging
import os

import httpx
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

SEARXNG_BASE_URL = os.getenv("SEARXNG_BASE_URL", "http://searxng:8080")


def _search_searxng(query: str, max_results: int) -> str | None:
    """Try SearXNG. Returns formatted results or None on failure."""
    try:
        params = {"q": query, "format": "json", "count": max_results}
        resp = httpx.get(
            f"{SEARXNG_BASE_URL}/search", params=params, timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])[:max_results]
        if not results:
            return None
        output = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "No title")
            url = r.get("url", "")
            snippet = r.get("content", "")[:200]
            output.append(f"{i}. [{title}]({url})\n   {snippet}")
        return "\n\n".join(output)
    except (httpx.ConnectError, httpx.TimeoutException):
        logger.debug("SearXNG unavailable at %s, will fallback", SEARXNG_BASE_URL)
        return None
    except Exception as exc:
        logger.warning("SearXNG search failed: %s, will fallback", exc)
        return None


def _search_ddg(query: str, max_results: int) -> str:
    """Fallback: DuckDuckGo via ddgs package."""
    try:
        from ddgs import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))

        if not results:
            return "No results found."

        output = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "No title")
            url = r.get("href", "")
            snippet = r.get("body", "")[:200]
            output.append(f"{i}. [{title}]({url})\n   {snippet}")
        return "\n\n".join(output)
    except ImportError:
        logger.error("ddgs package not installed")
        return "Search failed: ddgs package not installed. Run: uv add ddgs"
    except Exception as exc:
        logger.error("DuckDuckGo search failed: %s", exc)
        return f"Search failed: {exc}"


@tool
def web_search_tool(query: str, max_results: int = 5) -> str:
    """Search the web. Uses SearXNG when available, falls back to DuckDuckGo."""
    # Try SearXNG first (available in Docker production)
    result = _search_searxng(query, max_results)
    if result is not None:
        return result

    # Fallback to DuckDuckGo (always available)
    logger.info("Using DuckDuckGo fallback for search")
    return _search_ddg(query, max_results)
