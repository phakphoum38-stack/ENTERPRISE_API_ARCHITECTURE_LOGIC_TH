from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable


class ToolRisk(str, Enum):
    READ_ONLY = "read-only"
    WRITE = "write"


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    capability: str
    description: str
    risk: ToolRisk = ToolRisk.READ_ONLY
    approval_required: bool = False


ToolHandler = Callable[[dict[str, object]], dict[str, object]]


class UnifiedToolRegistry:
    """Native V3 tool catalog with explicit risk and approval metadata."""

    def __init__(self) -> None:
        self._definitions: dict[str, ToolDefinition] = {}
        self._handlers: dict[str, ToolHandler] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.register(
            ToolDefinition(
                "echo",
                "utility",
                "Return the supplied text. Useful for deterministic tool-path validation.",
            ),
            lambda args: {"text": str(args.get("text", ""))},
        )
        self.register(
            ToolDefinition(
                "capacity-inspect",
                "orchestration",
                "Return a caller-supplied capacity snapshot without mutating state.",
            ),
            lambda args: dict(args),
        )
        self.register(
            ToolDefinition(
                "artifact-note",
                "artifacts",
                "Create a governed artifact note through a higher-level runtime handler.",
                risk=ToolRisk.WRITE,
                approval_required=True,
            )
        )

    def register(
        self,
        definition: ToolDefinition,
        handler: ToolHandler | None = None,
    ) -> None:
        if not definition.name or definition.name in self._definitions:
            raise ValueError(f"duplicate or empty tool: {definition.name}")
        self._definitions[definition.name] = definition
        if handler is not None:
            self._handlers[definition.name] = handler

    def list(self) -> tuple[ToolDefinition, ...]:
        return tuple(self._definitions[name] for name in sorted(self._definitions))

    def get(self, name: str) -> ToolDefinition | None:
        return self._definitions.get(name)

    def execute(
        self,
        name: str,
        arguments: dict[str, object] | None = None,
        *,
        approved: bool = False,
    ) -> dict[str, object]:
        definition = self._definitions.get(name)
        if definition is None:
            raise KeyError(name)
        if definition.approval_required and not approved:
            raise PermissionError(f"tool requires approval: {name}")
        handler = self._handlers.get(name)
        if handler is None:
            raise RuntimeError(f"tool requires runtime handler: {name}")
        return handler(dict(arguments or {}))
