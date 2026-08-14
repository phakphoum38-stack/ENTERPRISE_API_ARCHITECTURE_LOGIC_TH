from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

ToolHandler = Callable[[str], str]


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    handler: ToolHandler


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if not tool.name or tool.name in self._tools:
            raise ValueError(f"duplicate or empty tool: {tool.name}")
        self._tools[tool.name] = tool

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._tools))

    def resolve(self, requested: tuple[str, ...]) -> tuple[Tool, ...]:
        missing = [name for name in requested if name not in self._tools]
        if missing:
            raise KeyError(f"unknown tools: {', '.join(missing)}")
        return tuple(self._tools[name] for name in requested)
