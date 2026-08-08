#!/usr/bin/env python3
"""Cloud and service entrypoint for Research OS API with browser-safe CORS headers."""

from __future__ import annotations

import os
from http.server import ThreadingHTTPServer

from agent_server import AgentResearchOSHandler


class CloudResearchOSHandler(AgentResearchOSHandler):
    """Primary Research OS handler with Multi-Agent orchestration and CORS."""

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
