#!/usr/bin/env python3
"""Research OS AI Brain tool registry.

Tools are explicit runtime contracts. Metadata and adapters are registered
separately so the Brain can inspect permissions, side effects and capabilities
before any executable adapter is invoked. This module never discovers or runs
arbitrary shell commands on its own.
"""

from __future__ import annotations

import re
import threading
from collections.abc import Callable, Iterable, Mapping
from dataclasses import asdict, dataclass
from typing import Any


_TOOL_ID_RE = re.compile(r"^[a-z][a-z0-9_.-]{2,95}$")
_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][A-Za-z0-9_.-]+)?$")
TOOL_REGISTRY_CONTRACT = "brain-tools-phase-3"
ToolAdapter = Callable[[str, Mapping[str, Any], bool], Mapping[str, Any]]


@dataclass(frozen=True)
class ToolDefinition:
    tool_id: str
    version: str
    name: str
    description: str
    capabilities: tuple[str, ...]
    permissions: tuple[str, ...] = ()
    mutating: bool = False
    destructive: bool = False
    network: bool = False
    secret_access: bool = False
    idempotent: bool = True
    supports_dry_run: bool = True
    enabled: bool = True
    owner: str = "Research OS"


CORE_BRAIN_TOOLS: tuple[ToolDefinition, ...] = (
    ToolDefinition(
        "brain.skills.inspect",
        "1.0.0",
        "Brain Skill Inspector",
        "Read-only inspection of the Research OS Skill Registry.",
        ("skill_discovery", "skill_registry"),
        permissions=("runtime.read",),
        mutating=False,
        idempotent=True,
    ),
    ToolDefinition(
        "brain.session.inspect",
        "1.0.0",
        "Brain Session Inspector",
        "Read-only inspection of Brain working memory and activity for one session.",
        ("working_memory", "activity_ledger", "session_inspection"),
        permissions=("memory.read",),
        mutating=False,
        idempotent=True,
    ),
    ToolDefinition(
        "brain.context.inspect",
        "1.0.0",
        "Brain Context Inspector",
        "Builds a secret-redacted context snapshot without changing project state.",
        ("context_engine", "context_inspection"),
        permissions=("runtime.read",),
        mutating=False,
        idempotent=True,
    ),
)


class ToolRegistry:
    """Thread-safe tool metadata and adapter registry."""

    def __init__(self, tools: Iterable[ToolDefinition] = CORE_BRAIN_TOOLS) -> None:
        self._lock = threading.RLock()
        self._tools: dict[str, ToolDefinition] = {}
        self._adapters: dict[str, ToolAdapter] = {}
        for tool in tools:
            self.register(tool)

    @staticmethod
    def _validate(tool: ToolDefinition) -> None:
        if not _TOOL_ID_RE.fullmatch(tool.tool_id):
            raise ValueError(f"invalid tool_id: {tool.tool_id}")
        if not _VERSION_RE.fullmatch(tool.version):
            raise ValueError(f"invalid tool version: {tool.version}")
        if not tool.name.strip() or not tool.description.strip():
            raise ValueError(f"tool name/description required: {tool.tool_id}")
        if not tool.capabilities:
            raise ValueError(f"tool capabilities required: {tool.tool_id}")
        if tool.destructive and not tool.mutating:
            raise ValueError(f"destructive tool must be mutating: {tool.tool_id}")

    def register(self, tool: ToolDefinition, *, replace: bool = False) -> dict[str, Any]:
        self._validate(tool)
        with self._lock:
            if tool.tool_id in self._tools and not replace:
                raise ValueError(f"tool already registered: {tool.tool_id}")
            self._tools[tool.tool_id] = tool
            if replace and not tool.enabled:
                self._adapters.pop(tool.tool_id, None)
            return self.describe(tool.tool_id)

    def register_adapter(
        self,
        tool_id: str,
        adapter: ToolAdapter,
        *,
        replace: bool = False,
    ) -> dict[str, Any]:
        if not callable(adapter):
            raise ValueError("tool adapter must be callable")
        with self._lock:
            tool = self.get(tool_id)
            if not tool.enabled:
                raise ValueError(f"tool disabled: {tool_id}")
            if tool_id in self._adapters and not replace:
                raise ValueError(f"tool adapter already registered: {tool_id}")
            self._adapters[tool_id] = adapter
            return self.describe(tool_id)

    def unregister_adapter(self, tool_id: str) -> bool:
        with self._lock:
            self.get(tool_id)
            return self._adapters.pop(tool_id, None) is not None

    def get(self, tool_id: str) -> ToolDefinition:
        with self._lock:
            try:
                return self._tools[tool_id]
            except KeyError as exc:
                raise ValueError(f"unknown tool: {tool_id}") from exc

    def adapter(self, tool_id: str) -> ToolAdapter:
        with self._lock:
            tool = self.get(tool_id)
            if not tool.enabled:
                raise ValueError(f"tool disabled: {tool_id}")
            try:
                return self._adapters[tool_id]
            except KeyError as exc:
                raise ValueError(f"tool adapter unavailable: {tool_id}") from exc

    def describe(self, tool_id: str) -> dict[str, Any]:
        with self._lock:
            tool = self.get(tool_id)
            return {
                **asdict(tool),
                "adapter_ready": bool(tool.enabled and tool_id in self._adapters),
                "ready": bool(tool.enabled and tool_id in self._adapters),
            }

    def list(self) -> list[dict[str, Any]]:
        with self._lock:
            return [self.describe(tool_id) for tool_id in sorted(self._tools)]

    def discover(
        self,
        *,
        capability: str | None = None,
        permission: str | None = None,
        ready_only: bool = False,
    ) -> list[dict[str, Any]]:
        cap = capability.casefold().strip() if capability else None
        perm = permission.casefold().strip() if permission else None
        matches: list[dict[str, Any]] = []
        for item in self.list():
            if ready_only and not item["ready"]:
                continue
            if cap and cap not in {str(value).casefold() for value in item["capabilities"]}:
                continue
            if perm and perm not in {str(value).casefold() for value in item["permissions"]}:
                continue
            matches.append(item)
        return matches

    def invoke(
        self,
        tool_id: str,
        action: str,
        payload: Mapping[str, Any],
        *,
        dry_run: bool,
    ) -> dict[str, Any]:
        """Invoke an already-authorized adapter.

        Permission checks intentionally do not live here. The ExecutionController
        is the sole Brain Runtime authorization gate and calls this method only
        after policy, evidence and approval checks succeed.
        """
        tool = self.get(tool_id)
        if dry_run and not tool.supports_dry_run:
            raise ValueError(f"tool does not support dry-run: {tool_id}")
        adapter = self.adapter(tool_id)
        result = adapter(action, dict(payload), dry_run)
        if not isinstance(result, Mapping):
            raise TypeError(f"tool adapter must return a mapping: {tool_id}")
        return dict(result)

    def capability_catalog(self) -> dict[str, list[str]]:
        catalog: dict[str, list[str]] = {}
        for item in self.list():
            if not item["enabled"]:
                continue
            for capability in item["capabilities"]:
                catalog.setdefault(str(capability), []).append(str(item["tool_id"]))
        return {key: sorted(value) for key, value in sorted(catalog.items())}

    def dashboard(self) -> dict[str, Any]:
        tools = self.list()
        return {
            "registry": "research_os_tools",
            "contract": TOOL_REGISTRY_CONTRACT,
            "tool_count": len(tools),
            "enabled_count": sum(1 for item in tools if item["enabled"]),
            "ready_count": sum(1 for item in tools if item["ready"]),
            "mutating_count": sum(1 for item in tools if item["mutating"]),
            "capabilities": self.capability_catalog(),
            "tools": tools,
            "execution_boundary": "permissioned_execution_controller_only",
        }


TOOLS = ToolRegistry()
