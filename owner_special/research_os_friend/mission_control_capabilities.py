from __future__ import annotations

from typing import Any


class MissionControlCapabilities:
    """Read-only projection of the existing capability/tool health surfaces.

    This class is presentation-only: it consumes FriendRuntime's existing
    catalog and health snapshots and never executes, registers, or authorizes.
    """

    VERSION = 1
    MAX_ROWS = 100

    def __init__(self, runtime: Any) -> None:
        self.runtime = runtime

    def snapshot(self, *, limit: int = 25) -> dict[str, object]:
        if limit < 1 or limit > self.MAX_ROWS:
            raise ValueError(f"limit must be between 1 and {self.MAX_ROWS}")

        health = self.runtime.tool_health()
        rows = tuple(health.get("rows", ()))
        ordered = sorted(rows, key=lambda row: str(row.get("name", "")))[:limit]
        return {
            "schema": "research-os-mission-control-capabilities/v1",
            "owner_id": self.runtime.owner.owner_id,
            "read_only": True,
            "execution_authority": "FriendOrchestrator",
            "authorization_authority": "OwnerPolicy",
            "approval_authority": "ApprovalGate",
            "source": "UnifiedToolCatalog+ToolHealthMatrix+ToolHealthGate",
            "total": len(rows),
            "healthy": int(health.get("healthy", 0)),
            "counts": dict(health.get("counts", {})),
            "gate": dict(health.get("gate", {})),
            "rows": [dict(row) for row in ordered],
            "limit": limit,
            "truncated": len(rows) > len(ordered),
        }
