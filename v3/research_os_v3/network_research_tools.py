from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from .research_tools import ResearchTool, ToolRequest, ToolResult


class WebResearchTool:
    name = "web"
    capabilities = frozenset({"web.fetch"})

    def __init__(self, timeout: float = 10.0, max_bytes: int = 1_000_000) -> None:
        self.timeout = timeout
        self.max_bytes = max_bytes

    def execute(self, request: ToolRequest) -> ToolResult:
        url = str(request.input.get("url", ""))
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return ToolResult(self.name, False, error="InvalidUrl")
        try:
            response = urlopen(Request(url, headers={"User-Agent": "ResearchOS/1.0"}), timeout=self.timeout)
            body = response.read(self.max_bytes).decode("utf-8", errors="replace")
        except Exception as exc:
            return ToolResult(self.name, False, error=type(exc).__name__)
        return ToolResult(self.name, True, output=body, source_uri=url, metadata={"content_type": response.headers.get("Content-Type", "")})


class GitHubResearchTool:
    name = "github"
    capabilities = frozenset({"github.repository", "github.file"})

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def _get_json(self, url: str) -> Any:
        request = Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "ResearchOS/1.0"})
        with urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def execute(self, request: ToolRequest) -> ToolResult:
        owner = str(request.input.get("owner", ""))
        repo = str(request.input.get("repo", ""))
        if not owner or not repo or "/" in owner or "/" in repo:
            return ToolResult(self.name, False, error="InvalidRepository")
        if request.capability == "github.repository":
            url = f"https://api.github.com/repos/{quote(owner)}/{quote(repo)}"
        elif request.capability == "github.file":
            path = str(request.input.get("path", "")).strip("/")
            if not path:
                return ToolResult(self.name, False, error="MissingPath")
            url = f"https://api.github.com/repos/{quote(owner)}/{quote(repo)}/contents/{quote(path, safe='/')}"
        else:
            return ToolResult(self.name, False, error="UnsupportedCapability")
        try:
            data = self._get_json(url)
        except Exception as exc:
            return ToolResult(self.name, False, error=type(exc).__name__)
        return ToolResult(self.name, True, output=data, source_uri=url, metadata={"provider": "github-api"})
