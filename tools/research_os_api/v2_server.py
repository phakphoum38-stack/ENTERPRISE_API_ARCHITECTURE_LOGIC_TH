#!/usr/bin/env python3
"""Research OS API V2 compatibility and readiness facade.

V2 aliases use the same V1 runtime/orchestrator owners so state and business
logic remain single-source while clients migrate incrementally.
"""

from __future__ import annotations

from http import HTTPStatus
from urllib.parse import urlsplit, urlunsplit

from agent_server import AgentResearchOSHandler
from v2_observability import readiness_snapshot


class V2ResearchOSHandler(AgentResearchOSHandler):
    """Expose V2 aliases and consolidated readiness while preserving V1."""

    _v2_aliases = (
        ("/v2/orchestrations", "/v1/agents/orchestrations"),
        ("/v2/agents", "/v1/agents"),
    )

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        if parsed.path == "/v2/health/readiness":
            payload = readiness_snapshot()
            self._send(
                HTTPStatus.OK if payload["ready"] else HTTPStatus.SERVICE_UNAVAILABLE,
                payload,
            )
            return
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
