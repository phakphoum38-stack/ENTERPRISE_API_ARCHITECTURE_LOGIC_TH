#!/usr/bin/env python3
"""Cloud entrypoint for Research OS API with browser-safe CORS headers."""

from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from urllib.parse import urlsplit

from email_identity import (
    get_profile,
    request_code,
    update_preferences,
    verify_code,
)
from streaming_handler import StreamingResearchOSHandler


class CloudResearchOSHandler(StreamingResearchOSHandler):
    """Research OS handler configured for the public Flutter web client."""

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
        self.send_header("Access-Control-Expose-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "86400")
        super().end_headers()

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.end_headers()

    def _identity_authorization(self) -> str | None:
        return self.headers.get("Authorization")

    def do_GET(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        if path != "/v1/identity/profile":
            super().do_GET()
            return
        try:
            self._send(HTTPStatus.OK, get_profile(self._identity_authorization()))
        except PermissionError as exc:
            self._send(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized", "detail": str(exc)})
        except Exception as exc:
            self._send(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "identity_error", "detail": str(exc)})

    def do_POST(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        if not path.startswith("/v1/identity/"):
            super().do_POST()
            return
        try:
            body = self._read_json()
            if path == "/v1/identity/request-code":
                self._send(HTTPStatus.OK, request_code(str(body.get("email", ""))))
                return
            if path == "/v1/identity/verify-code":
                self._send(
                    HTTPStatus.OK,
                    verify_code(
                        str(body.get("challenge_id", "")),
                        str(body.get("code", "")),
                    ),
                )
                return
            if path == "/v1/identity/preferences":
                self._send(
                    HTTPStatus.OK,
                    update_preferences(
                        self._identity_authorization(),
                        body.get("preferences", {}),
                    ),
                )
                return
            self._send(HTTPStatus.NOT_FOUND, {"error": "not_found", "path": path})
        except PermissionError as exc:
            self._send(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized", "detail": str(exc)})
        except ValueError as exc:
            self._send(HTTPStatus.BAD_REQUEST, {"error": "bad_request", "detail": str(exc)})
        except RuntimeError as exc:
            self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "identity_not_configured", "detail": str(exc)})
        except Exception as exc:
            self._send(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "identity_error", "detail": str(exc)})


def main() -> int:
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8787"))
    server = ThreadingHTTPServer((host, port), CloudResearchOSHandler)
    print(f"Research OS cloud API listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
