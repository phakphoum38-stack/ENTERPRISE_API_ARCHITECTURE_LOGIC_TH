from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .approval import SIDE_EFFECT_TOOLS


@dataclass(frozen=True)
class McpToolDescriptor:
    name: str
    description: str
    server: str
    side_effect: bool = False
    capability: str = ""


@dataclass(frozen=True)
class McpDiscoveryResult:
    name: str
    server: str
    description: str
    capability: str
    approval_required: bool


class McpDiscoveryBoundary:
    """Read-only normalization boundary for future MCP tool discovery.

    This phase accepts descriptors only. It does not connect to MCP servers,
    invoke remote tools, or create an execution path around OwnerPolicy.
    """

    def discover(
        self,
        descriptors: Iterable[McpToolDescriptor],
        *,
        query: str = "",
        limit: int = 8,
    ) -> tuple[McpDiscoveryResult, ...]:
        if limit < 1:
            raise ValueError("limit must be >= 1")
        needle = query.strip().lower()
        results: list[McpDiscoveryResult] = []
        for item in descriptors:
            haystack = " ".join((item.name, item.description, item.server, item.capability)).lower()
            if needle and needle not in haystack:
                continue
            approval_required = item.side_effect or item.name in SIDE_EFFECT_TOOLS
            results.append(
                McpDiscoveryResult(
                    name=item.name,
                    server=item.server,
                    description=item.description,
                    capability=item.capability,
                    approval_required=approval_required,
                )
            )
        results.sort(key=lambda item: (item.server, item.name))
        return tuple(results[:limit])

    def execution_status(self) -> dict[str, object]:
        return {
            "discovery": "ready",
            "transport": "disabled",
            "remote_execution": False,
            "approval_bypass": False,
            "execution_authority": "FriendOrchestrator",
            "authorization_authority": "OwnerPolicy",
        }
