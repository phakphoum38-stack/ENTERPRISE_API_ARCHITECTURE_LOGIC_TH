from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

from .drive_runtime import DriveToolRuntimeAdapter
from .workspace_runtime import WorkspaceRuntime


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

    def __init__(self, drive_runtime: DriveToolRuntimeAdapter | None = None) -> None:
        self._definitions: dict[str, ToolDefinition] = {}
        self._handlers: dict[str, ToolHandler] = {}
        self.drive_runtime = drive_runtime or DriveToolRuntimeAdapter()
        self.workspace_runtime = WorkspaceRuntime()
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
        self.register(
            ToolDefinition(
                "drive-tools-list",
                "drive-runtime",
                "List checksum-governed tool packages from the configured local Google Drive mirror.",
            ),
            lambda args: {
                "status": self.drive_runtime.status(),
                "packages": self.drive_runtime.discover(),
            },
        )
        self.register(
            ToolDefinition(
                "drive-tool-execute",
                "drive-runtime",
                "Execute a verified Drive tool package without a shell through the local mirror adapter.",
                risk=ToolRisk.WRITE,
                approval_required=True,
            ),
            self.drive_runtime.execute,
        )

        self.register(
            ToolDefinition("workspace-status", "workspace", "Inspect the configured Research OS Drive workspace."),
            lambda args: self.workspace_runtime.status(),
        )
        self.register(
            ToolDefinition("workspace-files-list", "files", "List files inside DRIVE_VIRTUAL_CLOUD with strict path confinement."),
            self.workspace_runtime.list_files,
        )
        self.register(
            ToolDefinition("workspace-file-read", "files", "Preview a bounded UTF-8 text file inside DRIVE_VIRTUAL_CLOUD."),
            self.workspace_runtime.read_text,
        )
        self.register(
            ToolDefinition("workspace-repositories", "repositories", "Inventory repository snapshots and bundle hashes from the Drive mirror."),
            lambda args: {"repositories": self.workspace_runtime.repositories()},
        )
        self.register(
            ToolDefinition("github-status", "github", "Inspect the local GitHub repository mirror without requiring network access."),
            lambda args: self.workspace_runtime.github_status(),
        )
        self.register(
            ToolDefinition("drive-status", "drive", "Inspect DRIVE_VIRTUAL_CLOUD and its top-level directories."),
            lambda args: self.workspace_runtime.drive_status(),
        )
        self.register(
            ToolDefinition("runtime-status", "runtime", "Inspect the running Research OS service runtime."),
            lambda args: self.workspace_runtime.runtime_status(),
        )
        self.register(
            ToolDefinition("installer-status", "installer", "Inspect the installed Research OS runtime location and build metadata."),
            lambda args: self.workspace_runtime.installer_status(),
        )
        self.register(
            ToolDefinition("backups-list", "backup", "List Research OS backup archives visible in the Drive mirror."),
            lambda args: {"backups": self.workspace_runtime.backups()},
        )
        self.register(
            ToolDefinition(
                "research-shell",
                "diagnostics",
                "Run the bounded Research OS diagnostic command console; arbitrary OS shell execution is disabled.",
            ),
            self.workspace_runtime.shell,
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
