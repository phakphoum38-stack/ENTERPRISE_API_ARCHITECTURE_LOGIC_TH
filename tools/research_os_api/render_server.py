#!/usr/bin/env python3
"""Cloud and service entrypoint for Research OS API with browser-safe CORS headers."""

from __future__ import annotations

import os
from http.server import ThreadingHTTPServer

from v2_server import V2ResearchOSHandler


class CloudResearchOSHandler(V2ResearchOSHandler):
    """Primary Research OS handler with V1 compatibility and V2 namespace."""

    def end_headers(self) -> None:
        configured_origins = os.getenv(
            "RESEARCH_OS_ALLOWED_ORIGINS",
            "https://phakphum12345.github.io,https://phakphoum38-stack.github.io",
        )
        allowed_origins = {item.strip() for item in configured_origins.split(",") if item.strip()}
        request_origin = (self.headers.get("Origin") or "").strip()
        if request_origin in allowed_origins:
            self.send_header("Access-Control-Allow-Origin", request_origin)
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, Authorization, X-Research-OS-Sync-Key, X-Research-OS-Session, X-Research-OS-OAuth-State",
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
