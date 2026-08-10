#!/usr/bin/env python3
"""Cloud and service entrypoint for Research OS API with browser-safe CORS headers."""

from __future__ import annotations

import os
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from urllib.parse import urlsplit

from v2_server import V2ResearchOSHandler
from v2_service_auth import ServiceExposureAuthError, verify_service_request


class CloudResearchOSHandler(V2ResearchOSHandler):
    """Primary Research OS handler with V1 compatibility and V2 namespace."""

    def _authorize_exposure(self) -> bool:
        if urlsplit(self.path).path == "/health":
            return True
        try:
            bind_host = str(self.server.server_address[0])
            verify_service_request(
                {name: value for name, value in self.headers.items()},
                bind_host=bind_host,
            )
            return True
        except ServiceExposureAuthError as exc:
            self._v2_request = self.path.startswith("/v2/")
            self._send(
                HTTPStatus.UNAUTHORIZED,
                {
                    "error": "service_identity_required",
                    "detail": str(exc),
                },
            )
            return False

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
            "Content-Type, Authorization, X-Research-OS-Sync-Key, "
            "X-ResearchOS-Principal, X-ResearchOS-Identity-Timestamp, "
            "X-ResearchOS-Identity-Nonce, X-ResearchOS-Identity-Signature",
        )
        self.send_header("Access-Control-Max-Age", "86400")
        super().end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if self._authorize_exposure():
            super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        if self._authorize_exposure():
            super().do_POST()

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.end_headers()


def main() -> int:
    host = os.getenv("HOST", "127.0.0.1")
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
