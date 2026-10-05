from __future__ import annotations

from typing import Any, Mapping

from tools.research_os_api.adapter_runtime_security import AdapterRuntimeSecurityBoundary
from tools.research_os_api.auth_session import verify_session
from v3.research_os_v3.network_research_tools import GitHubResearchTool, WebResearchTool
from v3.research_os_v3.research_tool_adapters import BuiltinResearchTools, ToolRequest as AdapterToolRequest
from v3.research_os_v3.research_tools import ResearchToolError, ResearchToolRegistry, ToolRequest, ToolResult


class _BuiltinResearchToolAdapter:
    """Translate the local adapter contract into the V3 ResearchTool contract."""

    def __init__(self, builtin: BuiltinResearchTools, name: str, action: str) -> None:
        self._builtin = builtin
        self.name = name
        self.capabilities = frozenset({f"{name}.{action}"})
        self._action = action

    def execute(self, request: ToolRequest) -> ToolResult:
        result = self._builtin.execute(
            AdapterToolRequest(
                tool=self.name,
                action=self._action,
                arguments=request.input,
            )
        )
        return ToolResult(
            tool_name=self.name,
            success=result.success,
            output=result.data,
            source_uri=result.source_uri,
            error=result.error,
        )


class V3ExecutionAdapter:
    """Controlled execution boundary from Friend into the V3 tool registry.

    Friend keeps request/owner policy decisions; V3 keeps tool execution ownership.
    Network tools are registered but never invoked during construction.
    """

    ALLOWED_CAPABILITIES = frozenset(
        {
            "web.fetch",
            "github.repository",
            "github.file",
            "file.read",
            "python.analyze",
            "shell.run",
        }
    )

    TOOL_REQUEST_NAMES = {
        "web.fetch": "web",
        "github.repository": "github",
        "github.file": "github",
        "file.read": "file",
        "python.analyze": "python",
        "shell.run": "shell",
    }

    def __init__(self, registry: ResearchToolRegistry | None = None) -> None:
        self._builtin = BuiltinResearchTools()
        self._security_boundary = AdapterRuntimeSecurityBoundary()
        self.registry = registry or self._build_default_registry(self._builtin)

    @classmethod
    def _build_default_registry(cls, builtin: BuiltinResearchTools | None = None) -> ResearchToolRegistry:
        registry = ResearchToolRegistry()
        builtin = builtin or BuiltinResearchTools()
        registry.register(WebResearchTool())
        registry.register(GitHubResearchTool())
        registry.register(_BuiltinResearchToolAdapter(builtin, "file", "read"))
        registry.register(_BuiltinResearchToolAdapter(builtin, "python", "analyze"))
        registry.register(_BuiltinResearchToolAdapter(builtin, "shell", "run"))
        return registry

    def names(self) -> tuple[str, ...]:
        return self.registry.names()

    def capabilities(self) -> tuple[str, ...]:
        return tuple(sorted(self.ALLOWED_CAPABILITIES))

    def execute(
        self,
        *,
        owner_id: str,
        request_owner_id: str,
        requested_tools: tuple[str, ...],
        capability: str,
        input: Mapping[str, Any],
        task_id: str | None = None,
        session_token: str | None = None,
    ) -> ToolResult:
        if owner_id != request_owner_id:
            raise PermissionError("V3 tool request owner does not match configured owner")
        if capability not in self.ALLOWED_CAPABILITIES:
            raise PermissionError(f"V3 capability is not allowed: {capability}")
        expected_tool = self.TOOL_REQUEST_NAMES[capability]
        if expected_tool not in requested_tools and capability not in requested_tools:
            raise PermissionError(f"V3 capability was not explicitly requested: {capability}")
        if not session_token:
            raise PermissionError("canonical Research OS session token is required")
        principal = verify_session(session_token)
        if str(principal.get("user_id") or "") != owner_id:
            raise PermissionError("canonical session owner does not match V3 owner")
        if expected_tool in {"file", "python", "shell"}:
            result, _decision = self._builtin.execute_authorized(
                AdapterToolRequest(
                    tool=expected_tool,
                    action=capability.split(".", 1)[1],
                    arguments=input,
                ),
                principal=principal,
                session_token=session_token,
                request_id=task_id or f"v3-{capability}",
                policy_decision="ALLOW",
                security_boundary=self._security_boundary,
            )
            return ToolResult(
                tool_name=expected_tool,
                success=result.success,
                output=result.data,
                source_uri=result.source_uri,
                error=result.error,
            )
        try:
            return self.registry.execute(ToolRequest(capability, input, task_id=task_id))
        except ResearchToolError:
            raise

    def snapshot(self) -> dict[str, object]:
        return {
            "available": True,
            "tools": self.names(),
            "capabilities": self.capabilities(),
            "policy": "canonical-session + owner-match + explicit-tool-request + capability-allowlist + adapter-runtime-boundary",
        }
