from __future__ import annotations

import json
from html.parser import HTMLParser
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .tools import Tool, ToolRegistry


MAX_BYTES = 1_000_000
DEFAULT_TIMEOUT = 10.0


class _TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "title":
            self.in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.parts.append(data)

    @property
    def title(self) -> str:
        return " ".join("".join(self.parts).split())


def _web_fetch(text: str) -> str:
    url = (text or "").strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return json.dumps({"error": "InvalidUrl"}, ensure_ascii=False)
    try:
        request = Request(url, headers={"User-Agent": "ResearchOS/1.0"})
        with urlopen(request, timeout=DEFAULT_TIMEOUT) as response:
            body = response.read(MAX_BYTES).decode("utf-8", errors="replace")
            content_type = response.headers.get("Content-Type", "")
    except Exception as exc:
        return json.dumps({"error": type(exc).__name__}, ensure_ascii=False)

    parser = _TitleParser()
    if "html" in content_type.lower() or "<html" in body[:1000].lower():
        parser.feed(body)
    return json.dumps(
        {
            "url": url,
            "content_type": content_type,
            "title": parser.title,
            "body": body,
        },
        ensure_ascii=False,
    )


def install_web_tool(registry: ToolRegistry) -> ToolRegistry:
    registry.register(
        Tool(
            "web.fetch",
            "Read public HTTP(S) resources with a bounded response size.",
            _web_fetch,
        )
    )
    return registry
