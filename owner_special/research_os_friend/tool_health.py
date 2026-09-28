from __future__ import annotations

from typing import Iterable, Mapping

from .unified_tool_catalog import UnifiedToolCatalog


class ToolHealthMatrix:
    """Read-only system health view over registered Friend and V3 tools."""

    def __init__(self, catalog: UnifiedToolCatalog | None = None) -> None:
        self.catalog = catalog or UnifiedToolCatalog()

    def snapshot(
        self,
        *,
        friend_tools: Iterable[str] = (),
        v3_tools: Iterable[str] = (),
    ) -> dict[str, object]:
        rows = self.catalog.health_matrix(
            friend_tools=friend_tools,
            v3_tools=v3_tools,
        )
        counts: dict[str, int] = {}
        for row in rows:
            state = str(row["state"])
            counts[state] = counts.get(state, 0) + 1
        return {
            "total": len(rows),
            "counts": counts,
            "healthy": counts.get("ready", 0),
            "rows": rows,
        }
