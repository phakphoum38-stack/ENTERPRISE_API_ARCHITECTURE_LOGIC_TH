#!/usr/bin/env python3
"""Research OS API V2 compatibility facade.

The V2 handler preserves all V1 routes and maps the new V2 namespace onto the
same runtime/orchestrator owners. This avoids duplicating state or business
logic while clients migrate incrementally.
"""

from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit

from agent_server import AgentResearchOSHandler


class V2ResearchOSHandler(AgentResearchOSHandler):
    """Expose versioned V2 aliases while keeping V1 fully compatible."""

    _v2_aliases = (
        ("/v2/orchestrations", "/v1/agents/orchestrations"),
        ("/v2/agents", "/v1/agents"),
    )

    def do_GET(self) -> None:  # noqa: N802
        self._rewrite_v2_path()
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        self._rewrite_v2_path()
        super().do_POST()

    def _rewrite_v2_path(self) -> None:
        parsed = urlsplit(self.path)
        rewritten = parsed.path
        for source, target in self._v2_aliases:
            if rewritten == source or rewritten.startswith(source + "/"):
                rewritten = target + rewritten[len(source) :]
                break
        if rewritten == parsed.path:
            return
        self.path = urlunsplit(
            (parsed.scheme, parsed.netloc, rewritten, parsed.query, parsed.fragment)
        )


__all__ = ["V2ResearchOSHandler"]
