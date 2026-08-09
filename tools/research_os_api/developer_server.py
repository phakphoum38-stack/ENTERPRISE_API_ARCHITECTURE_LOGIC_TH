#!/usr/bin/env python3
"""Separate Research OS Developer Platform API.

Authentication is delegated to a trusted identity gateway. This service accepts
identity headers only when the gateway also presents the configured shared
secret. It stores access-request/grant metadata only; canonical user files and
ownership remain unchanged.
"""

from __future__ import annotations

import hmac
import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from developer_access import DeveloperAccessStore


class DeveloperPlatformHandler(BaseHTTPRequestHandler):
    server_version = "ResearchOSDeveloper/2.0"

    def _store(self) -> DeveloperAccessStore:
        data_dir = os.environ.get("RESEARCH_OS_DATA_DIR") or str(Path.home() / "ResearchOSData")
        return DeveloperAccessStore(data_dir)

    def _principal(self) -> str:
        configured = (os.environ.get("RESEARCH_OS_IDENTITY_PROXY_SECRET") or "").strip()
        if not configured:
            raise PermissionError("trusted identity gateway is not configured")
        supplied = (self.headers.get("X-ResearchOS-Identity-Secret") or "").strip()
        if not supplied or not hmac.compare_digest(configured, supplied):
            raise PermissionError("trusted identity gateway verification failed")
        principal = (self.headers.get("X-ResearchOS-Principal") or "").strip()
        if not principal:
            raise PermissionError("authenticated principal is missing")
        return principal

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return {}
        if length > 1024 * 1024:
            raise ValueError("request body is too large")
        raw = self.rfile.read(length)
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("JSON body must be an object")
        return payload

    def _send(self, status: HTTPStatus | int, payload: dict[str, Any]) -> None:
        body = json.dumps({"api_version": "v2", **payload}, ensure_ascii=False).encode("utf-8")
        self.send_response(int(status))
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status: HTTPStatus | int, code: str, message: str) -> None:
        self._send(status, {"error": {"code": code, "message": message, "status": int(status)}})

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        if parsed.path == "/health":
            self._send(HTTPStatus.OK, {"status": "ok", "service": "research-os-developer-api"})
            return
        try:
            principal = self._principal()
            query = parse_qs(parsed.query)
            if parsed.path == "/v2/developer/access-requests":
                view = (query.get("view") or ["developer"])[0].strip().lower()
                if view == "owner":
                    status = (query.get("status") or [None])[0]
                    items = self._store().list_owner_requests(principal, status=status)
                elif view == "developer":
                    items = self._store().list_developer_requests(principal)
                else:
                    raise ValueError("view must be owner or developer")
                self._send(HTTPStatus.OK, {"items": items, "count": len(items), "view": view})
                return
            if parsed.path == "/v2/developer/grants":
                items = self._store().list_developer_grants(principal, active_only=True)
                self._send(HTTPStatus.OK, {"items": items, "count": len(items)})
                return
            self._error(HTTPStatus.NOT_FOUND, "not_found", parsed.path)
        except PermissionError as exc:
            self._error(HTTPStatus.UNAUTHORIZED, "identity_required", str(exc))
        except (TypeError, ValueError) as exc:
            self._error(HTTPStatus.BAD_REQUEST, "bad_request", str(exc))

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        try:
            principal = self._principal()
            body = self._read_json()
            store = self._store()

            if parsed.path == "/v2/developer/access-requests":
                item = store.request_access(
                    developer_id=principal,
                    owner_id=str(body.get("owner_id") or ""),
                    workspace_id=str(body.get("workspace_id") or ""),
                    resource_id=str(body.get("resource_id") or ""),
                    resource_name=str(body.get("resource_name") or ""),
                    requested_scopes=list(body.get("scopes") or []),
                    purpose=str(body.get("purpose") or ""),
                )
                self._send(HTTPStatus.CREATED, {"request": item, "access_active": False})
                return

            request_prefix = "/v2/developer/access-requests/"
            if parsed.path.startswith(request_prefix):
                relative = parsed.path[len(request_prefix) :].strip("/")
                parts = relative.split("/") if relative else []
                if len(parts) == 2 and parts[1] in {"approve", "reject", "cancel"}:
                    request_id, action = parts
                    if action == "approve":
                        expires = body.get("expires_in_seconds")
                        grant = store.approve_request(
                            owner_id=principal,
                            request_id=request_id,
                            scopes=list(body.get("scopes") or []) or None,
                            expires_in_seconds=int(expires) if expires is not None else None,
                        )
                        self._send(HTTPStatus.OK, {"grant": grant})
                    elif action == "reject":
                        item = store.reject_request(
                            owner_id=principal,
                            request_id=request_id,
                            reason=str(body.get("reason") or ""),
                        )
                        self._send(HTTPStatus.OK, {"request": item})
                    else:
                        item = store.cancel_request(developer_id=principal, request_id=request_id)
                        self._send(HTTPStatus.OK, {"request": item})
                    return

            grant_prefix = "/v2/developer/grants/"
            if parsed.path.startswith(grant_prefix) and parsed.path.endswith("/revoke"):
                grant_id = parsed.path[len(grant_prefix) : -len("/revoke")].strip("/")
                item = store.revoke_grant(
                    owner_id=principal,
                    grant_id=grant_id,
                    reason=str(body.get("reason") or ""),
                )
                self._send(HTTPStatus.OK, {"grant": item})
                return

            if parsed.path == "/v2/developer/authorize":
                decision = store.authorize(
                    principal_id=principal,
                    owner_id=str(body.get("owner_id") or ""),
                    workspace_id=str(body.get("workspace_id") or ""),
                    resource_id=str(body.get("resource_id") or ""),
                    scope=str(body.get("scope") or "read"),
                )
                self._send(HTTPStatus.OK, {"authorization": decision})
                return

            self._error(HTTPStatus.NOT_FOUND, "not_found", parsed.path)
        except PermissionError as exc:
            self._error(HTTPStatus.FORBIDDEN, "permission_denied", str(exc))
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            self._error(HTTPStatus.BAD_REQUEST, "bad_request", str(exc))
        except (OSError, RuntimeError) as exc:
            self._error(HTTPStatus.SERVICE_UNAVAILABLE, "developer_access_unavailable", str(exc))

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"developer-api {self.address_string()} - {fmt % args}")


def main() -> int:
    host = os.environ.get("RESEARCH_OS_DEVELOPER_HOST", "127.0.0.1")
    port = int(os.environ.get("RESEARCH_OS_DEVELOPER_PORT", "8790"))
    server = ThreadingHTTPServer((host, port), DeveloperPlatformHandler)
    print(f"Research OS Developer Platform API listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
