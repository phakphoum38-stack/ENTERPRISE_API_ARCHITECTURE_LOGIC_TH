from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ToolHealth:
    name: str
    status: str
    source: str
    detail: str


class ToolHealthGate:
    """Deterministic read-only health classification for Friend and V3 tools."""

    def inspect(self, *, friend_tools: Iterable[str], v3_tools: Iterable[str]) -> tuple[ToolHealth, ...]:
        friend = set(friend_tools)
        v3 = set(v3_tools)
        rows: list[ToolHealth] = []
        rows.append(ToolHealth("web.fetch", "READY" if "web.fetch" in friend or "web" in v3 else "MISSING", "friend/v3", "public HTTP(S) reader"))
        rows.append(ToolHealth("github.repository_status", "READY" if "github.repository_status" in friend else "MISSING", "friend", "read-only repository dashboard"))
        rows.append(ToolHealth("github.repository", "READY" if "github" in v3 else "MISSING", "v3", "GitHub repository API"))
        rows.append(ToolHealth("github.file", "READY" if "github" in v3 else "MISSING", "v3", "GitHub file API"))
        rows.append(ToolHealth("file.read", "READY" if "file" in v3 else "MISSING", "v3", "local file reader"))
        rows.append(ToolHealth("python.analyze", "READY" if "python" in v3 else "MISSING", "v3", "bounded Python tool"))
        rows.append(ToolHealth("shell.run", "READY" if "shell" in v3 else "MISSING", "v3", "policy-gated shell tool"))
        rows.append(ToolHealth("response", "READY", "friend", "provider response + verified tool results"))
        return tuple(rows)

    def snapshot(self, *, friend_tools: Iterable[str], v3_tools: Iterable[str]) -> dict[str, object]:
        rows = self.inspect(friend_tools=friend_tools, v3_tools=v3_tools)
        counts = {"READY": 0, "DEGRADED": 0, "BLOCKED": 0, "MISSING": 0}
        for row in rows:
            counts[row.status] = counts.get(row.status, 0) + 1
        return {
            "overall": "READY" if counts["MISSING"] == 0 and counts["BLOCKED"] == 0 else "DEGRADED",
            "counts": counts,
            "tools": [row.__dict__ for row in rows],
        }
