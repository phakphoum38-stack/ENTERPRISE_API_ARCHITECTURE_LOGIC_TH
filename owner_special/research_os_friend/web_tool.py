from __future__ import annotations

from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .tools import Tool, ToolRegistry


MAX_BYTES = 1_000_000
DEFAULT_TIMEOUT = 10.0


def _web_fetch(text: str) -> str:
    url = (text or "").strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return "web.fetch: InvalidUrl"
    try:
        request = Request(url, headers={"User-Agent": "ResearchOS/1.0"})
        with urlopen(request, timeout=DEFAULT_TIMEOUT) as response:
            body = response.read(MAX_BYTES).decode("utf-8", errors="replace")
            content_type = response.headers.get("Content-Type", "")
    except Exception as exc:
        return f"web.fetch: {type(exc).__name__}"
    return f"web.fetch: {url}\nContent-Type: {content_type}\n{body}"


def install_web_tool(registry: ToolRegistry) -> ToolRegistry:
    registry.register(
        Tool(
            "web.fetch",
            "Read public HTTP(S) resources with a bounded response size.",
            _web_fetch,
        )
    )
    return registry
