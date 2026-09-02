from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class ToolState(str, Enum):
    READY = "ready"
    IMPLEMENTED_UNREGISTERED = "implemented_unregistered"
    EXTERNAL = "external"
    NEEDS_CONNECTION = "needs_connection"


@dataclass(frozen=True)
class ToolDescriptor:
    name: str
    capability: str
    source: str
    state: ToolState
    optional: bool = False
    dependency: str | None = None


# This is metadata only: execution remains owned by the existing registries.
TOOL_CATALOG: tuple[ToolDescriptor, ...] = (
    ToolDescriptor("echo", "friend.echo", "friend", ToolState.READY),
    ToolDescriptor("summarize", "friend.summarize", "friend", ToolState.READY),
    ToolDescriptor("schedule.generate", "calendar.schedule.generate", "friend", ToolState.READY),
    ToolDescriptor("calendar.health", "calendar.health", "friend", ToolState.READY, True, "phakphum-calendar"),
    ToolDescriptor("calendar.sync", "calendar.sync", "friend", ToolState.READY, True, "phakphum-calendar"),
    ToolDescriptor("calendar.sync.status", "calendar.sync.status", "friend", ToolState.READY, True, "phakphum-calendar"),
    ToolDescriptor("web", "web.fetch", "v3", ToolState.IMPLEMENTED_UNREGISTERED),
    ToolDescriptor("github", "github.repository", "v3", ToolState.IMPLEMENTED_UNREGISTERED),
    ToolDescriptor("file", "file.read", "v3", ToolState.IMPLEMENTED_UNREGISTERED),
    ToolDescriptor("python", "python.analyze", "v3", ToolState.IMPLEMENTED_UNREGISTERED),
    ToolDescriptor("shell", "shell.run", "v3", ToolState.IMPLEMENTED_UNREGISTERED),
    ToolDescriptor("github-actions", "github.actions", "repair", ToolState.EXTERNAL, False, "GitHub"),
    ToolDescriptor("github-repository", "github.repository.manage", "repair", ToolState.EXTERNAL, False, "GitHub"),
    ToolDescriptor("yaml-validator", "validation.yaml", "repair", ToolState.READY),
    ToolDescriptor("python-validator", "validation.python", "repair", ToolState.READY),
    ToolDescriptor("git-branch", "git.branch", "repair", ToolState.READY),
    ToolDescriptor("pr-gate", "git.pull_request", "repair", ToolState.READY),
    ToolDescriptor("google-workspace", "google.workspace", "external", ToolState.NEEDS_CONNECTION, True, "Google Workspace"),
    ToolDescriptor("microsoft", "microsoft.oauth", "external", ToolState.NEEDS_CONNECTION, True, "Microsoft OAuth"),
)


class UnifiedToolCatalog:
    """Read-only catalog over Friend, V3, and repair tool surfaces."""

    def __init__(self, descriptors: Iterable[ToolDescriptor] = TOOL_CATALOG) -> None:
        self._descriptors = tuple(descriptors)
        names = [item.name for item in self._descriptors]
        if len(names) != len(set(names)):
            raise ValueError("duplicate tool catalog entry")

    def all(self) -> tuple[ToolDescriptor, ...]:
        return tuple(sorted(self._descriptors, key=lambda item: item.name))

    def by_state(self, state: ToolState) -> tuple[ToolDescriptor, ...]:
        return tuple(item for item in self.all() if item.state is state)

    def capabilities(self) -> tuple[str, ...]:
        return tuple(sorted({item.capability for item in self._descriptors}))

    def health_matrix(
        self,
        *,
        friend_tools: Iterable[str] = (),
        v3_tools: Iterable[str] = (),
    ) -> tuple[dict[str, object], ...]:
        friend = set(friend_tools)
        v3 = set(v3_tools)
        rows: list[dict[str, object]] = []
        for item in self.all():
            state = item.state
            if item.source == "friend" and item.name not in friend:
                state = ToolState.IMPLEMENTED_UNREGISTERED
            elif item.source == "v3" and item.name not in v3:
                state = ToolState.IMPLEMENTED_UNREGISTERED
            rows.append(
                {
                    "name": item.name,
                    "capability": item.capability,
                    "source": item.source,
                    "state": state.value,
                    "optional": item.optional,
                    "dependency": item.dependency,
                }
            )
        return tuple(rows)
