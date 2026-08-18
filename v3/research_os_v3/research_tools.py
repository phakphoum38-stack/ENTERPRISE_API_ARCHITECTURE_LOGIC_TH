from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class ToolRequest:
    capability: str
    input: Mapping[str, Any]
    task_id: str | None = None


@dataclass(frozen=True)
class ToolResult:
    tool_name: str
    success: bool
    output: Any = None
    source_uri: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)
    error: str | None = None


class ResearchTool(Protocol):
    name: str
    capabilities: frozenset[str]

    def execute(self, request: ToolRequest) -> ToolResult:
        ...


class ResearchToolError(ValueError):
    pass


class ResearchToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ResearchTool] = {}

    def register(self, tool: ResearchTool) -> None:
        if not tool.name.strip():
            raise ResearchToolError("tool name must not be empty")
        if tool.name in self._tools:
            raise ResearchToolError(f"tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> ResearchTool:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise ResearchToolError(f"unknown research tool: {name}") from exc

    def resolve(self, capability: str) -> tuple[ResearchTool, ...]:
        return tuple(
            tool for tool in self._tools.values() if capability in tool.capabilities
        )

    def execute(self, request: ToolRequest) -> ToolResult:
        candidates = self.resolve(request.capability)
        if not candidates:
            raise ResearchToolError(
                f"no research tool supports capability: {request.capability}"
            )
        return candidates[0].execute(request)

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._tools))
