from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol
import ast
import subprocess
import sys

from tools.research_os_api.adapter_runtime_security import AdapterRuntimeDecision, AdapterRuntimeSecurityBoundary


@dataclass(frozen=True)
class ToolRequest:
    tool: str
    action: str
    arguments: Mapping[str, Any]


@dataclass(frozen=True)
class ToolResult:
    tool: str
    action: str
    success: bool
    data: Any = None
    error: str | None = None
    source_uri: str | None = None


class ResearchToolAdapter(Protocol):
    name: str

    def execute(self, request: ToolRequest) -> ToolResult: ...


class FileResearchTool:
    name = "file"

    def execute(self, request: ToolRequest) -> ToolResult:
        if request.action != "read":
            return ToolResult(self.name, request.action, False, error="UnsupportedAction")
        path = Path(str(request.arguments.get("path", ""))).expanduser()
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            return ToolResult(self.name, request.action, False, error=type(exc).__name__)
        return ToolResult(self.name, request.action, True, data=text, source_uri=path.resolve().as_uri())


class PythonResearchTool:
    name = "python"

    def execute(self, request: ToolRequest) -> ToolResult:
        if request.action != "analyze":
            return ToolResult(self.name, request.action, False, error="UnsupportedAction")
        source = str(request.arguments.get("source", ""))
        try:
            tree = ast.parse(source, mode="exec")
        except SyntaxError as exc:
            return ToolResult(self.name, request.action, False, error=f"SyntaxError:{exc.lineno}")
        return ToolResult(
            self.name,
            request.action,
            True,
            data={
                "node_count": sum(1 for _ in ast.walk(tree)),
                "imports": [n.names[0].name for n in ast.walk(tree) if isinstance(n, ast.Import) and n.names],
            },
        )


class ShellResearchTool:
    name = "shell"

    def __init__(self, allowed_commands: tuple[str, ...] = ("python", "python3")) -> None:
        self.allowed_commands = allowed_commands

    def execute(self, request: ToolRequest) -> ToolResult:
        if request.action != "run":
            return ToolResult(self.name, request.action, False, error="UnsupportedAction")
        command = request.arguments.get("command")
        if not isinstance(command, list) or not command or command[0] not in self.allowed_commands:
            return ToolResult(self.name, request.action, False, error="CommandNotAllowed")
        try:
            completed = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return ToolResult(self.name, request.action, False, error=type(exc).__name__)
        return ToolResult(
            self.name,
            request.action,
            completed.returncode == 0,
            data={"stdout": completed.stdout, "stderr": completed.stderr, "returncode": completed.returncode},
        )


class BuiltinResearchTools:
    """Minimal local adapters. Network adapters can be registered separately."""

    def __init__(self) -> None:
        self._tools: dict[str, ResearchToolAdapter] = {
            "file": FileResearchTool(),
            "python": PythonResearchTool(),
            "shell": ShellResearchTool(),
        }

    def register(self, adapter: ResearchToolAdapter) -> None:
        self._tools[adapter.name] = adapter

    def execute(
        self,
        request: ToolRequest,
        *,
        authorization: AdapterRuntimeDecision | None = None,
    ) -> ToolResult:
        """Execute only after the canonical runtime security decision.

        Direct adapter execution is deliberately fail-closed. Callers must use
        execute_authorized() or provide the exact ALLOW decision returned by
        AdapterRuntimeSecurityBoundary for this request.
        """
        if authorization is None or not authorization.allowed:
            return ToolResult(request.tool, request.action, False, error="AuthorizationRequired")
        expected_capability = f"{request.tool}.{request.action}"
        if authorization.capability != expected_capability or authorization.adapter != request.tool:
            return ToolResult(request.tool, request.action, False, error="AuthorizationBindingMismatch")
        adapter = self._tools.get(request.tool)
        if adapter is None:
            return ToolResult(request.tool, request.action, False, error="ToolNotFound")
        return adapter.execute(request)

    def execute_authorized(
        self,
        request: ToolRequest,
        *,
        principal: Mapping[str, Any],
        request_id: str,
        policy_decision: str,
        security_boundary: AdapterRuntimeSecurityBoundary | None = None,
    ) -> tuple[ToolResult, AdapterRuntimeDecision]:
        """Cross the security wall, then execute through this existing registry."""
        capability = f"{request.tool}.{request.action}"
        gate = security_boundary or AdapterRuntimeSecurityBoundary()
        decision = gate.enforce(
            principal=principal,
            capability=capability,
            requested_tools=(request.tool,),
            arguments=request.arguments,
            request_id=request_id,
            policy_decision=policy_decision,
        )
        return self.execute(request, authorization=decision), decision
