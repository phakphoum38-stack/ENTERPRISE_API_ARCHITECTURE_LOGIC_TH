#!/usr/bin/env python3
"""Separate Research OS Developer Platform API.

Authenticated Developer access is delegated to a trusted identity gateway and
requires owner approval for real resources. A registration-free Trial Mode is
also available, but it is isolated to synthetic demo resources and cannot read
or mutate canonical user files, access grants, ownership, or source control.
"""

from __future__ import annotations

import hmac
import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlsplit

from developer_access import DeveloperAccessStore


TRIAL_RESOURCES: tuple[dict[str, Any], ...] = (
    {
        "resource_id": "demo-api-client",
        "workspace_id": "trial-workspace",
        "kind": "code",
        "name": "api_client.py",
        "language": "python",
        "summary": "Synthetic read-only API client example.",
        "content": "def get_health(client):\n    return client.get('/health')\n",
    },
    {
        "resource_id": "demo-openapi",
        "workspace_id": "trial-workspace",
        "kind": "api",
        "name": "openapi-demo.yaml",
        "language": "yaml",
        "summary": "Synthetic API contract example for Developer Trial Mode.",
        "content": "openapi: 3.1.0\ninfo:\n  title: Trial API\n  version: demo\n",
    },
    {
        "resource_id": "demo-readme",
        "workspace_id": "trial-workspace",
        "kind": "document",
        "name": "README.md",
        "language": "markdown",
        "summary": "Trial workspace guide. No owner files are exposed.",
        "content": "# Developer Trial\nRead-only synthetic workspace.\n",
    },
)

TRIAL_CAPABILITIES = {
    "registration_required": False,
    "persistent_account": False,
    "workspace": "trial-workspace",
    "allowed": ["browse_demo_resources", "read_demo_resource", "search_demo_resources", "simulate_read_authorization"],
    "restricted": ["real_file_access", "write", "delete", "commit", "owner_approval", "grant_management", "private_workspace_access"],
    "data_source": "synthetic_demo_only",
}


class DeveloperPlatformHandler(BaseHTTPRequestHandler):
    server_version = "ResearchOSDeveloper/2.0"

    def _store(self) -> DeveloperAccessStore:
        data_dir = os.environ.get("RESEARCH_OS_DATA_DIR") or str(Path.home() / "ResearchOSData")
        return DeveloperAccessStore(data_dir)

    @staticmethod
    def _app_dir() -> Path:
        return Path(__file__).resolve().parents[2] / "apps" / "research_os_developer"

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
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, path: Path) -> None:
        try:
            body = path.read_bytes()
        except OSError:
            self._error(HTTPStatus.NOT_FOUND, "ui_not_found", path.name)
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:",
        )
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status: HTTPStatus | int, code: str, message: str) -> None:
        self._send(status, {"error": {"code": code, "message": message, "status": int(status)}})

    @staticmethod
    def _trial_resource(resource_id: str) -> dict[str, Any] | None:
        return next((dict(item) for item in TRIAL_RESOURCES if item["resource_id"] == resource_id), None)

    def _trial_get(self, parsed) -> bool:
        path = parsed.path
        if path == "/v2/developer/trial":
            self._send(HTTPStatus.OK, {"mode": "trial", **TRIAL_CAPABILITIES})
            return True
        if path == "/v2/developer/trial/resources":
            query = (parse_qs(parsed.query).get("q") or [""])[0].strip().casefold()
            items = [dict(item) for item in TRIAL_RESOURCES]
            if query:
                items = [
                    item for item in items
                    if query in " ".join((item["name"], item["kind"], item["language"], item["summary"])).casefold()
                ]
            summaries = [{key: value for key, value in item.items() if key != "content"} for item in items]
            self._send(HTTPStatus.OK, {"mode": "trial", "items": summaries, "count": len(summaries), "query": query})
            return True
        prefix = "/v2/developer/trial/resources/"
        if path.startswith(prefix):
            resource_id = unquote(path[len(prefix):]).strip("/")
            item = self._trial_resource(resource_id)
            if item is None:
                self._error(HTTPStatus.NOT_FOUND, "trial_resource_not_found", resource_id)
            else:
                self._send(HTTPStatus.OK, {"mode": "trial", "resource": item, "read_only": True})
            return True
        return False

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        if parsed.path == "/health":
            self._send(HTTPStatus.OK, {"status": "ok", "service": "research-os-developer-api"})
            return
        if parsed.path in {"/trial", "/trial/"}:
            self._send_html(self._app_dir() / "index.html")
            return
        if parsed.path in {"/app", "/app/"}:
            self._send_html(self._app_dir() / "app.html")
            return
        if parsed.path == "/v2/developer/auth/config":
            self._send(
                HTTPStatus.OK,
                {
                    "login_url": (os.environ.get("RESEARCH_OS_DEVELOPER_LOGIN_URL") or "/app").strip(),
                    "identity_provider": "trusted_gateway",
                    "registration_required": True,
                },
            )
            return
        if self._trial_get(parsed):
            return
        try:
            principal = self._principal()
            query = parse_qs(parsed.query)
            if parsed.path == "/v2/developer/session":
                self._send(
                    HTTPStatus.OK,
                    {
                        "authenticated": True,
                        "principal": principal,
                        "identity_provider": "trusted_gateway",
                    },
                )
                return
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
            body = self._read_json()
            if parsed.path == "/v2/developer/trial/authorize":
                resource_id = str(body.get("resource_id") or "").strip()
                scope = str(body.get("scope") or "read").strip().lower()
                if scope != "read":
                    self._error(HTTPStatus.FORBIDDEN, "trial_restricted", "Trial Mode permits read simulation only")
                    return
                item = self._trial_resource(resource_id)
                if item is None:
                    self._error(HTTPStatus.NOT_FOUND, "trial_resource_not_found", resource_id)
                    return
                self._send(
                    HTTPStatus.OK,
                    {
                        "mode": "trial",
                        "authorization": {
                            "allowed": True,
                            "scope": "read",
                            "resource_id": resource_id,
                            "persistent": False,
                            "real_resource": False,
                        },
                    },
                )
                return
            if parsed.path.startswith("/v2/developer/trial/"):
                self._error(
                    HTTPStatus.FORBIDDEN,
                    "trial_restricted",
                    "Trial Mode cannot write, delete, commit, approve, or manage grants",
                )
                return

            principal = self._principal()
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
                relative = parsed.path[len(request_prefix):].strip("/")
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
                grant_id = parsed.path[len(grant_prefix):-len("/revoke")].strip("/")
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
