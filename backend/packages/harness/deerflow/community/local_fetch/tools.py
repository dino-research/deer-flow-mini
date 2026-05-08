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
