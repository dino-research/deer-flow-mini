"""Local web page fetcher using httpx + readabilipy."""

import ipaddress
import logging
import os
import socket

import httpx
from langchain_core.tools import tool
from markdownify import markdownify as md

logger = logging.getLogger(__name__)

MAX_RESULT_CHARS = int(os.getenv("WEB_FETCH_MAX_CHARS", "16000"))
MAX_DOWNLOAD_BYTES = int(os.getenv("WEB_FETCH_MAX_BYTES", str(5 * 1024 * 1024)))  # 5 MB

# Private / reserved IP ranges that must never be fetched.
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def _is_url_safe(url: str) -> tuple[bool, str]:
    """Validate a URL against SSRF risks.

    Returns (is_safe, reason) — reason is empty when safe.
    """
    from urllib.parse import urlparse

    parsed = urlparse(url)

    # Scheme check
    if parsed.scheme not in ("http", "https"):
        return False, f"Blocked scheme: {parsed.scheme}"

    hostname = parsed.hostname
    if not hostname:
        return False, "Missing hostname"

    # Resolve hostname to IP(s) and check each one.
    try:
        infos = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror:
        return False, f"Cannot resolve hostname: {hostname}"

    for _family, _type, _proto, _canonname, sockaddr in infos:
        ip = ipaddress.ip_address(sockaddr[0])
        for net in _BLOCKED_NETWORKS:
            if ip in net:
                return False, f"Blocked private/reserved IP: {ip}"

    return True, ""


@tool
def web_fetch_tool(url: str) -> str:
    """Fetch a web page and return its content as Markdown."""
    # ── SSRF guard ──────────────────────────────────────────────────────────
    safe, reason = _is_url_safe(url)
    if not safe:
        logger.warning("SSRF blocked: %s — %s", url, reason)
        return f"Refused to fetch {url}: {reason}"

    # ── Bounded streaming download ──────────────────────────────────────────
    try:
        collected = bytearray()
        with httpx.stream(
            "GET",
            url,
            timeout=20,
            follow_redirects=True,
            headers={"User-Agent": "DeerFlow-Mini/1.0"},
        ) as resp:
            resp.raise_for_status()
            for chunk in resp.iter_bytes():
                collected.extend(chunk)
                if len(collected) > MAX_DOWNLOAD_BYTES:
                    logger.warning(
                        "Truncating download from %s at %d bytes",
                        url,
                        MAX_DOWNLOAD_BYTES,
                    )
                    break

        html = collected.decode("utf-8", errors="replace")

        # ── Readability extraction ──────────────────────────────────────────
        from readabilipy import simple_json_from_html_string

        article = simple_json_from_html_string(html, use_readability=True)
        content = article.get("plain_content") or article.get("content", "")
        if content:
            result = md(content, strip=["img", "script", "style"])
        else:
            result = md(html, strip=["img", "script", "style"])

        return result[:MAX_RESULT_CHARS]

    except httpx.HTTPStatusError as exc:
        logger.error("HTTP %d fetching %s", exc.response.status_code, url)
        return f"Failed to fetch {url}: HTTP {exc.response.status_code}"
    except Exception as exc:
        logger.error("Web fetch failed for %s: %s", url, exc)
        return f"Failed to fetch {url}: {exc}"
