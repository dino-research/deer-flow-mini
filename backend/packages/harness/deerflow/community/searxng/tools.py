"""SearXNG web search tool for deer-flow-mini."""

import logging
import os

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
    except httpx.HTTPStatusError as exc:
        logger.error("SearXNG search failed with HTTP %d", exc.response.status_code)
        return f"Search failed: HTTP {exc.response.status_code}"
    except httpx.ConnectError:
        logger.error("Cannot connect to SearXNG at %s", SEARXNG_BASE_URL)
        return f"Search failed: cannot connect to SearXNG at {SEARXNG_BASE_URL}"
    except Exception as exc:
        logger.error("SearXNG search failed: %s", exc)
        return f"Search failed: {exc}"
