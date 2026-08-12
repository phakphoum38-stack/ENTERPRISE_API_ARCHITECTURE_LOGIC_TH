#!/usr/bin/env python3
"""Cloud and service entrypoint for Research OS API with browser-safe CORS headers."""

from __future__ import annotations

import os
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from provider_readiness import inspect_all
from v2_server import V2ResearchOSHandler


_ASSISTANT_BRANCHING = 6
_ASSISTANT_6X3_CAPACITY = _ASSISTANT_BRANCHING ** 3
_ASSISTANT_6X6_CAPACITY = _ASSISTANT_BRANCHING ** 6


class CloudResearchOSHandler(V2ResearchOSHandler):
    """Primary Research OS handler with V1 compatibility and V2 namespace."""

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)

        if parsed.path == "/v2/master":
            self._v2_request = True
            self._send(
                HTTPStatus.OK,
                {
                    "master": {
                        "contract": "unified-master-orchestrator-v3",
                        "architecture": "adaptive-hierarchical-ai-software-factory",
                        "provider_mode": "local_or_configured_provider",
                        "capacity": {
                            "branching_factor": _ASSISTANT_BRANCHING,
                            "assistant_levels": 3,
                            "max_levels": 6,
                            "assistant_6x3_capacity": _ASSISTANT_6X3_CAPACITY,
                            "max_leaf_capacity": _ASSISTANT_6X6_CAPACITY,
                        },
                        "state_owners": {
                            "orchestrator": "agent_server.ORCHESTRATOR",
                        },
                    }
                },
            )
            return

        if parsed.path == "/v2/brain/providers":
            self._v2_request = True
            self._send(HTTPStatus.OK, {"providers": inspect_all()})
            return

        super().do_GET()

    def log_message(self, format: str, *args: object) -> None:
        """Keep the normal HTTP log and a deterministic request-audit trail."""
        super().log_message(format, *args)
        data_dir = os.getenv("RESEARCH_OS_DATA_DIR")
        if not data_dir:
            return
        audit_path = Path(data_dir) / "logs" / "request-audit.log"
        try:
            audit_path.parent.mkdir(parents=True, exist_ok=True)
            with audit_path.open("a", encoding="utf-8") as stream:
                stream.write((format % args) + "\n")
        except OSError:
            # Request handling must never fail because diagnostic evidence could
            # not be written.
            pass

    def end_headers(self) -> None:
        allowed_origin = os.getenv(
            "RESEARCH_OS_ALLOWED_ORIGIN",
            "https://phakphoum38-stack.github.io",
        )
        self.send_header("Access-Control-Allow-Origin", allowed_origin)
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, Authorization, X-Research-OS-Sync-Key",
        )
        self.send_header("Access-Control-Max-Age", "86400")
        super().end_headers()

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.end_headers()


def main() -> int:
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8787"))
    server = ThreadingHTTPServer((host, port), CloudResearchOSHandler)
    print(f"Research OS primary API listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
