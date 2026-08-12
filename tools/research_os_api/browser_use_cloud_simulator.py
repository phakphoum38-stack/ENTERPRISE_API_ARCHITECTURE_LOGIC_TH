#!/usr/bin/env python3
"""Tiny local Browser Use Cloud simulator for quota-free CI smoke tests."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import unquote, urlsplit


class BrowserUseCloudSimulatorHandler(BaseHTTPRequestHandler):
    server_version = "BrowserUseCloudSimulator/0.1"
    sessions: dict[str, dict[str, Any]] = {}

    def _send(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("JSON body must be an object")
        return payload

    def do_GET(self) -> None:  # noqa: N802
        if urlsplit(self.path).path == "/health":
            self._send(HTTPStatus.OK, {"status": "ok", "sessions": len(self.sessions)})
            return
        self._send(HTTPStatus.NOT_FOUND, {"error": "not_found", "path": self.path})

    def do_POST(self) -> None:  # noqa: N802
        try:
            path = urlsplit(self.path).path
            if path != "/api/v4/browsers":
                self._send(HTTPStatus.NOT_FOUND, {"error": "not_found", "path": path})
                return

            api_key = self.headers.get("X-Browser-Use-API-Key", "").strip()
            if not api_key:
                self._send(HTTPStatus.UNAUTHORIZED, {"error": "missing_api_key"})
                return

            body = self._read_json()
            proxy = str(body.get("proxyCountryCode") or "us").strip().lower()[:2] or "us"
            browser_id = f"sim-{uuid.uuid4().hex[:12]}"
            cdp_url = f"wss://simulated.browser-use.local/devtools/{browser_id}"
            self.sessions[browser_id] = {
                "id": browser_id,
                "cdpUrl": cdp_url,
                "proxyCountryCode": proxy,
                "status": "running",
            }
            self._send(HTTPStatus.CREATED, {"id": browser_id, "cdpUrl": cdp_url})
        except (ValueError, json.JSONDecodeError) as exc:
            self._send(HTTPStatus.BAD_REQUEST, {"error": "bad_request", "detail": str(exc)})

    def do_PATCH(self) -> None:  # noqa: N802
        try:
            prefix = "/api/v4/browsers/"
            path = urlsplit(self.path).path
            if not path.startswith(prefix):
                self._send(HTTPStatus.NOT_FOUND, {"error": "not_found", "path": path})
                return

            browser_id = unquote(path[len(prefix) :])
            body = self._read_json()
            if body.get("action") != "stop":
                self._send(HTTPStatus.BAD_REQUEST, {"error": "unsupported_action"})
                return

            session = self.sessions.get(browser_id)
            if not session:
                self._send(HTTPStatus.NOT_FOUND, {"error": "browser_not_found", "id": browser_id})
                return

            session["status"] = "stopped"
            self._send(HTTPStatus.OK, {"id": browser_id, "status": "stopped"})
        except (ValueError, json.JSONDecodeError) as exc:
            self._send(HTTPStatus.BAD_REQUEST, {"error": "bad_request", "detail": str(exc)})

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("[browser-use-sim] " + (fmt % args) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a local Browser Use Cloud API simulator.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8799)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), BrowserUseCloudSimulatorHandler)
    print(f"Browser Use Cloud simulator listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
