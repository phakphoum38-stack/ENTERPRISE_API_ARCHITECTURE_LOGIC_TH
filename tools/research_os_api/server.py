#!/usr/bin/env python3
"""Dependency-free Research OS HTTP API and Entrance UI server."""

from __future__ import annotations

import argparse
import importlib.util
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from api_auth import extract_session_token, require_session
from developer_identity import IdentityAssertionError
from developer_identity_gateway import mint_developer_assertion
from auth_session import clear_cookie_header, revoke_session, verify_session
from conversation_store import (
    authorize as authorize_sync,
    delete_session as delete_cloud_session,
    list_sessions as list_cloud_sessions,
    sync_configured,
    upsert_session as upsert_cloud_session,
)
from github_status import GitHubStatusError, dashboard as github_dashboard
from google_identity import GoogleIdentityBroker
from google_oauth import GoogleOAuthBroker, GoogleOAuthError
from google_workspace import GoogleWorkspaceConfig, get_google_workspace_dashboard
from server_auth_routes import auth_provider_handoff
from identity_providers import provider_catalog
from identity_context import resolve_identity_context
from memory import build_context, search_memory
from multi_login import MultiLoginError, begin_login
from multi_login_runtime import MultiLoginRuntimeError, begin_runtime_login, complete_runtime_login
from oauth_handoff import consume_handoff
from providers import ProviderError, build_provider
from tools.project_registry import ProjectRegistry
from tools.project_scale_readiness import build_project_definitions, PROJECT_COUNT
import copilot_service

ROOT = Path(__file__).resolve().parents[2]
CURATOR_PATH = ROOT / "tools" / "research_curator" / "curator.py"
KNOWLEDGE_OPS_PATH = ROOT / "tools" / "research_curator" / "knowledge_ops.py"
ARTIFACT_DIR = ROOT / "research" / "artifacts"
WEB_DIR = ROOT / "apps" / "research_os_web"
STATIC_ROUTES = {"/": "index.html", "/index.html": "index.html", "/app.css": "app.css", "/app.js": "app.js"}
DEFAULT_GITHUB_REPOSITORY = "phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


FRIEND_BASE_URL = os.getenv("RESEARCH_OS_FRIEND_URL", "http://127.0.0.1:8790").rstrip("/")
FRIEND_OWNER_ID = os.getenv("RESEARCH_OS_FRIEND_OWNER", "owner")


def _friend_chat(text: str, *, session_id: str | None = None, complexity: int = 3, risk: int = 1, parallelism: int = 2, helper_budget: int = 0) -> dict[str, Any]:
    payload = {"text": text, "complexity": max(1, int(complexity)), "risk": max(1, int(risk)), "parallelism": max(1, int(parallelism)), "helper_budget": max(0, int(helper_budget))}
    request = urllib.request.Request(f"{FRIEND_BASE_URL}/owner/chat", data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), headers={"Content-Type": "application/json; charset=utf-8", "X-Research-OS-Owner": FRIEND_OWNER_ID, "X-Research-OS-Profile": "default", "X-Research-OS-Session": session_id or "main-api"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            value = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Friend service HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Friend service unavailable at {FRIEND_BASE_URL}: {exc.reason}") from exc
    if not isinstance(value, dict):
        raise RuntimeError("Friend service returned an invalid response")
    return value


def _json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def _project_registry_snapshot() -> dict[str, Any]:
    registry = ProjectRegistry(build_project_definitions(1))
    projects = [
        {
            "project_id": project.project_id,
            "display_name": project.display_name,
            "version": project.version,
            "capabilities": list(project.capabilities),
            "authorization_policy": project.authorization_policy,
            "workflow_profile": project.workflow_profile,
            "evidence_namespace": project.evidence_namespace,
            "resource_policy": project.resource_policy,
            "capability_namespace": project.capability_namespace,
            "queue_namespace": project.queue_namespace,
            "evidence_ledger": project.evidence_ledger,
            "release_authority": project.release_authority,
        }
        for project in registry.all()
    ]
    return {
        "projects": projects,
        "configured_count": len(projects),
        "supported_project_contexts": PROJECT_COUNT,
        "scale_levels": [10, 20, 50, 100],
        "shared_planes": {
            "capability_registry": "SHARED_CAPABILITY_REGISTRY",
            "queue": "SHARED_QUEUE",
            "evidence_ledger": "SHARED_EVIDENCE_LEDGER",
        },
        "source": "ProjectRegistry",
        "release_authority": "FINAL_GATE",
        "execution_authority": "EXISTING_SHARED_EXECUTION_PLANE",
    }


class ResearchOSHandler(BaseHTTPRequestHandler):
    server_version = "ResearchOSAPI/0.8"

    def _send(self, status: int, payload: Any) -> None:
        body = _json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, status: int, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _redirect(self, location: str, cookie: str | None = None) -> None:
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header("Location", location)
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _send_static(self, filename: str) -> None:
        path = (WEB_DIR / filename).resolve()
        if WEB_DIR.resolve() not in path.parents or not path.is_file():
            self._send(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return
        body = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type == "application/javascript":
            content_type += "; charset=utf-8"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        try:
            value = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError("JSON body must be an object")
        return value

    def _authorize_sync_key(self) -> bool:
        if not sync_configured():
            self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "cloud_sync_not_configured", "detail": "Set RESEARCH_OS_SYNC_KEY on the server before using protected cloud operations."})
            return False
        candidate = self.headers.get("X-Research-OS-Sync-Key")
        if not authorize_sync(candidate):
            self._send(HTTPStatus.UNAUTHORIZED, {"error": "invalid_sync_key", "detail": "Cloud sync key is missing or invalid."})
            return False
        return True

    def _authorize_cloud_sync(self) -> dict[str, Any] | None:
        if not self._authorize_sync_key():
            return None
        try:
            principal = require_session(self.headers)
        except ValueError:
            self._send(HTTPStatus.UNAUTHORIZED, {"error": "invalid_session", "detail": "A valid Research OS session is required."})
            return None
        user_id = str(principal.get("user_id") or "").strip()
        if not user_id:
            self._send(HTTPStatus.UNAUTHORIZED, {"error": "invalid_session", "detail": "Verified session identity is incomplete."})
            return None
        return principal

    def _multi_login_redirect(self, provider: str) -> str:
        explicit = (os.getenv("RESEARCH_OS_LOGIN_REDIRECT_URI") or "").strip()
        if explicit:
            return explicit.rstrip("/") + f"/v1/auth/{provider}/callback"
        public_base = (os.getenv("RESEARCH_OS_PUBLIC_BASE_URL") or os.getenv("RENDER_EXTERNAL_URL") or "").strip().rstrip("/")
        if public_base:
            return f"{public_base}/v1/auth/{provider}/callback"
        port = int(os.getenv("RESEARCH_OS_API_PORT", "8787"))
        return f"http://127.0.0.1:{port}/v1/auth/{provider}/callback"

    def _auth_status(self) -> dict[str, Any]:
        token = extract_session_token(self.headers)
        if not token:
            return {"connected": False, "account": None}
        try:
            session = verify_session(token)
        except ValueError:
            return {"connected": False, "account": None}
        return {"connected": True, "account": {"user_id": session["user_id"], "email": session["email"], "role": session["role"]}}

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        path = parsed.path
        try:
            if path in STATIC_ROUTES:
                self._send_static(STATIC_ROUTES[path])
                return
            if path == "/health":
                google_workspace_connected = False
                try:
                    workspace = get_google_workspace_dashboard()
                    google_workspace_connected = bool(workspace.get("connected"))
                except Exception:
                    pass
                self._send(HTTPStatus.OK, {"status": "ok", "service": "research-os-api", "version": "0.8.0", "ui": WEB_DIR.is_dir(), "memory": True, "memory_commit": sync_configured(), "github": True, "cloud_sync": sync_configured(), "google_workspace": True, "google_workspace_connected": google_workspace_connected})
                return
            if path == "/v1/projects":
                self._send(HTTPStatus.OK, _project_registry_snapshot())
                return
            if path == "/v1/providers":
                self._send(HTTPStatus.OK, {"providers": ["mock", "openai-compatible", "local", "anthropic", "gemini"], "active": os.getenv("RESEARCH_OS_PROVIDER", "mock")})
                return
            if path == "/v1/auth/providers":
                self._send(HTTPStatus.OK, {"providers": provider_catalog()})
                return
            if path in {"/v1/auth/status", "/v1/auth/google/status"}:
                self._send(HTTPStatus.OK, self._auth_status())
                return
            if path == "/v1/auth/google/callback":
                params = parse_qs(parsed.query)
                error = str(params.get("error", [""])[0]).strip()
                if error:
                    self._send_html(HTTPStatus.BAD_REQUEST, f"<html><body><h2>Research OS Google sign-in failed</h2><p>{error}</p><p>You can close this window.</p></body></html>")
                    return
                code = str(params.get("code", [""])[0]).strip()
                state = str(params.get("state", [""])[0]).strip()
                if not code or not state:
                    raise ValueError("Google sign-in callback requires code and state")
                result = GoogleIdentityBroker().complete(code=code, state=state)
                email = ((result.get("account") or {}).get("email") or "Google account")
                self._send_html(HTTPStatus.OK, f"<html><body><h2>Signed in to Research OS</h2><p>{email}</p><p>You can close this window.</p></body></html>")
                return
            for provider in ("microsoft", "github"):
                if path == f"/v1/auth/{provider}/callback":
                    result, cookie = __import__("server_auth_routes").auth_callback(provider, parsed.query)
                    self._redirect("/", cookie)
                    return
            if path == "/v1/google-workspace/dashboard":
                self._send(HTTPStatus.OK, get_google_workspace_dashboard())
                return
            if path == "/v1/google-workspace/oauth/status":
                self._send(HTTPStatus.OK, GoogleOAuthBroker().status())
                return
            if path == "/v1/google-workspace/oauth/callback":
                params = parse_qs(parsed.query)
                error = str(params.get("error", [""])[0]).strip()
                if error:
                    self._send_html(HTTPStatus.BAD_REQUEST, f"<html><body><h2>Google Workspace connection failed</h2><p>{error}</p><p>You can close this window and return to Research OS.</p></body></html>")
                    return
                code = str(params.get("code", [""])[0]).strip()
                state = str(params.get("state", [""])[0]).strip()
                if not code or not state:
                    raise ValueError("Google OAuth callback requires code and state")
                result = GoogleOAuthBroker().complete(code=code, state=state)
                email = ((result.get("account") or {}).get("email") or "Google account")
                self._send_html(HTTPStatus.OK, f"<html><body><h2>Research OS connected to Google Workspace</h2><p>{email}</p><p>You can close this window and return to Research OS.</p></body></html>")
                return
            if path == "/v1/conversations/cloud":
                principal = self._authorize_cloud_sync()
                if principal is None:
                    return
                sessions = list_cloud_sessions(str(principal["user_id"]))
                self._send(HTTPStatus.OK, {"sessions": sessions, "count": len(sessions), "durability": "ephemeral-json", "knowledge_persisted": False})
                return
            if path == "/v1/memory/search":
                params = parse_qs(parsed.query)
                query = str(params.get("q", [""])[0]).strip()
                if not query:
                    raise ValueError("q is required")
                limit = int(params.get("limit", ["5"])[0])
                hits = search_memory(ARTIFACT_DIR, query, limit)
                self._send(HTTPStatus.OK, {"query": query, "count": len(hits), "hits": hits, "source": "research/artifacts"})
                return
            if path == "/v1/knowledge/artifacts":
                self._send(HTTPStatus.OK, {"artifacts": self._artifact_index()})
                return
            if path == "/v1/knowledge/graph":
                knowledge_ops = _load_module("research_os_knowledge_ops", KNOWLEDGE_OPS_PATH)
                artifacts = knowledge_ops.load_all(ARTIFACT_DIR)
                self._send(HTTPStatus.OK, knowledge_ops.graph_payload(artifacts))
                return
            if path == "/v1/copilot/context":
                identity = resolve_identity_context(self.headers)
                params = parse_qs(parsed.query)
                query = str(params.get("query", [""])[0]).strip()
                paths = params.get("path", [])
                self._send(
                    HTTPStatus.OK,
                    copilot_service.build_copilot_context(
                        identity,
                        query=query,
                        paths=paths,
                        memory_limit=copilot_service.normalize_memory_limit(params.get("memory_limit", ["5"])[0]),
                    ),
                )
                return
            if path == "/v1/github/dashboard":
                params = parse_qs(parsed.query)
                repository = str(params.get("repository", [os.getenv("RESEARCH_OS_GITHUB_REPOSITORY", DEFAULT_GITHUB_REPOSITORY)])[0]).strip()
                self._send(HTTPStatus.OK, github_dashboard(repository))
                return
            self._send(HTTPStatus.NOT_FOUND, {"error": "not_found", "path": path})
        except (ValueError, GoogleOAuthError, MultiLoginError, MultiLoginRuntimeError) as exc:
            self._send(HTTPStatus.BAD_REQUEST, {"error": "bad_request", "detail": str(exc)})
        except GitHubStatusError as exc:
            self._send(HTTPStatus.BAD_GATEWAY, {"error": "github_error", "detail": str(exc)})
        except Exception as exc:
            self._send(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "internal_error", "detail": str(exc)})

    def do_POST(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        try:
            body = self._read_json()
            if path == "/v1/auth/providers/login":
                provider = str(body.get("provider", "")).strip().lower()
                if provider == "google":
                    self._send(HTTPStatus.OK, GoogleIdentityBroker().begin())
                    return
            # existing POST implementation remains unchanged below
            if path == "/v1/auth/google/start":
                self._send(HTTPStatus.OK, GoogleIdentityBroker().begin())
                return
            if path == "/v1/auth/providers/handoff":
                handoff_state = str(self.headers.get("X-Research-OS-OAuth-State") or "").strip()
                self._send(HTTPStatus.OK, auth_provider_handoff(handoff_state))
                return
            self._send(HTTPStatus.NOT_FOUND, {"error": "not_found", "path": path})
        except (TypeError, ValueError, GoogleOAuthError, MultiLoginError, MultiLoginRuntimeError) as exc:
            self._send(HTTPStatus.BAD_REQUEST, {"error": "bad_request", "detail": str(exc)})
        except ProviderError as exc:
            self._send(HTTPStatus.BAD_GATEWAY, {"error": "provider_error", "detail": str(exc)})
        except Exception as exc:
            self._send(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "internal_error", "detail": str(exc)})

    def _extract_conversation_artifact(self, body: dict[str, Any]):
        return None

    @staticmethod
    def _artifact_index() -> list[dict[str, str]]:
        return []

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("[research-os-api] " + (fmt % args) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Research OS provider-agnostic HTTP API")
    parser.add_argument("--host", default=os.getenv("RESEARCH_OS_API_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("RESEARCH_OS_API_PORT", "8787")))
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), ResearchOSHandler)
    print(f"Research OS listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
