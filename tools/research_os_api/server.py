#!/usr/bin/env python3
"""Dependency-free Research OS HTTP API and Entrance UI server."""

from __future__ import annotations

import argparse
import importlib.util
import json
import mimetypes
import os
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from conversation_store import (
    authorize as authorize_sync,
    delete_session as delete_cloud_session,
    list_sessions as list_cloud_sessions,
    sync_configured,
    upsert_session as upsert_cloud_session,
)
from github_status import GitHubStatusError, dashboard as github_dashboard
from google_oauth import GoogleOAuthBroker, GoogleOAuthError
from google_workspace import GoogleWorkspaceConfig, get_google_workspace_dashboard
from memory import build_context, search_memory
from providers import ProviderError, build_provider

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


def _json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


class ResearchOSHandler(BaseHTTPRequestHandler):
    server_version = "ResearchOSAPI/0.6"

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

    def _authorize_cloud_sync(self) -> bool:
        if not sync_configured():
            self._send(
                HTTPStatus.SERVICE_UNAVAILABLE,
                {
                    "error": "cloud_sync_not_configured",
                    "detail": "Set RESEARCH_OS_SYNC_KEY on the server before using protected cloud operations.",
                },
            )
            return False
        candidate = self.headers.get("X-Research-OS-Sync-Key")
        if not authorize_sync(candidate):
            self._send(
                HTTPStatus.UNAUTHORIZED,
                {"error": "invalid_sync_key", "detail": "Cloud sync key is missing or invalid."},
            )
            return False
        return True

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
                    # Google Workspace is optional. Liveness must not fail because
                    # an optional integration cannot initialize in service context.
                    pass
                self._send(
                    HTTPStatus.OK,
                    {
                        "status": "ok",
                        "service": "research-os-api",
                        "version": "0.6.0",
                        "ui": WEB_DIR.is_dir(),
                        "memory": True,
                        "memory_commit": sync_configured(),
                        "github": True,
                        "cloud_sync": sync_configured(),
                        "google_workspace": True,
                        "google_workspace_connected": google_workspace_connected,
                    },
                )
                return
            if path == "/v1/providers":
                self._send(
                    HTTPStatus.OK,
                    {
                        "providers": ["mock", "openai-compatible", "local", "anthropic", "gemini"],
                        "active": os.getenv("RESEARCH_OS_PROVIDER", "mock"),
                    },
                )
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
                    self._send_html(
                        HTTPStatus.BAD_REQUEST,
                        f"<html><body><h2>Google Workspace connection failed</h2><p>{error}</p><p>You can close this window.</p></body></html>",
                    )
                    return
                code = str(params.get("code", [""])[0]).strip()
                state = str(params.get("state", [""])[0]).strip()
                if not code or not state:
                    raise ValueError("Google OAuth callback requires code and state")
                result = GoogleOAuthBroker().complete(code=code, state=state)
                email = ((result.get("account") or {}).get("email") or "Google account")
                self._send_html(
                    HTTPStatus.OK,
                    f"<html><body><h2>Research OS connected to Google Workspace</h2><p>{email}</p><p>You can close this window and return to Research OS.</p></body></html>",
                )
                return
            if path == "/v1/conversations/cloud":
                if not self._authorize_cloud_sync():
                    return
                sessions = list_cloud_sessions()
                self._send(
                    HTTPStatus.OK,
                    {
                        "sessions": sessions,
                        "count": len(sessions),
                        "durability": "ephemeral-json",
                        "knowledge_persisted": False,
                    },
                )
                return
            if path == "/v1/memory/search":
                params = parse_qs(parsed.query)
                query = str(params.get("q", [""])[0]).strip()
                if not query:
                    raise ValueError("q is required")
                try:
                    limit = int(params.get("limit", ["5"])[0])
                except ValueError as exc:
                    raise ValueError("limit must be an integer") from exc
                hits = search_memory(ARTIFACT_DIR, query, limit)
                self._send(
                    HTTPStatus.OK,
                    {"query": query, "count": len(hits), "hits": hits, "source": "research/artifacts"},
                )
                return
            if path == "/v1/knowledge/artifacts":
                self._send(HTTPStatus.OK, {"artifacts": self._artifact_index()})
                return
            if path == "/v1/knowledge/graph":
                knowledge_ops = _load_module("research_os_knowledge_ops", KNOWLEDGE_OPS_PATH)
                artifacts = knowledge_ops.load_all(ARTIFACT_DIR)
                self._send(HTTPStatus.OK, knowledge_ops.graph_payload(artifacts))
                return
            if path == "/v1/github/dashboard":
                params = parse_qs(parsed.query)
                repository = str(
                    params.get(
                        "repository",
                        [os.getenv("RESEARCH_OS_GITHUB_REPOSITORY", DEFAULT_GITHUB_REPOSITORY)],
                    )[0]
                ).strip()
                self._send(HTTPStatus.OK, github_dashboard(repository))
                return
            self._send(HTTPStatus.NOT_FOUND, {"error": "not_found", "path": path})
        except (ValueError, GoogleOAuthError) as exc:
            self._send(HTTPStatus.BAD_REQUEST, {"error": "bad_request", "detail": str(exc)})
        except GitHubStatusError as exc:
            self._send(HTTPStatus.BAD_GATEWAY, {"error": "github_error", "detail": str(exc)})
        except Exception as exc:
            self._send(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "internal_error", "detail": str(exc)})

    def do_POST(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        try:
            body = self._read_json()
            if path == "/v1/google-workspace/oauth/start":
                self._send(HTTPStatus.OK, GoogleOAuthBroker().begin())
                return
            if path == "/v1/google-workspace/oauth/disconnect":
                self._send(HTTPStatus.OK, GoogleOAuthBroker().disconnect())
                return
            if path == "/v1/google-workspace/local/accept":
                self._send(HTTPStatus.OK, GoogleWorkspaceConfig().accept_local_account())
                return
            if path == "/v1/google-workspace/services":
                services = body.get("enabled_services")
                if not isinstance(services, list):
                    raise ValueError("enabled_services must be an array")
                config = GoogleWorkspaceConfig()
                config.set_enabled_services(str(item) for item in services)
                self._send(HTTPStatus.OK, config.dashboard())
                return
            if path == "/v1/conversations/cloud/sync":
                if not self._authorize_cloud_sync():
                    return
                session = body.get("session")
                if not isinstance(session, dict):
                    raise ValueError("session must be an object")
                saved = upsert_cloud_session(session)
                self._send(
                    HTTPStatus.OK,
                    {
                        "session": saved,
                        "synced": True,
                        "knowledge_persisted": False,
                    },
                )
                return
            if path == "/v1/conversations/cloud/delete":
                if not self._authorize_cloud_sync():
                    return
                session_id = str(body.get("session_id", "")).strip()
                deleted = delete_cloud_session(session_id)
                self._send(HTTPStatus.OK, {"session_id": session_id, "deleted": deleted})
                return
            if path == "/v1/ai/generate":
                prompt = str(body.get("prompt", "")).strip()
                if not prompt:
                    raise ValueError("prompt is required")
                result = build_provider(body.get("provider")).generate(
                    prompt,
                    system=str(body.get("system", "")),
                    model=body.get("model"),
                )
                self._send(
                    HTTPStatus.OK,
                    {
                        "provider": result.provider,
                        "model": result.model,
                        "text": result.text,
                        "session_id": body.get("session_id"),
                    },
                )
                return
            if path == "/v1/ai/answer-with-memory":
                question = str(body.get("question", "")).strip()
                if not question:
                    raise ValueError("question is required")
                limit = int(body.get("limit", 5))
                hits = search_memory(ARTIFACT_DIR, question, limit)
                context = build_context(hits)
                system = (
                    "Answer using the supplied Research OS memory. Distinguish stored facts from inference. "
                    "When memory is insufficient, say so. Do not invent artifact contents."
                )
                prompt = f"Memory:\n{context or '(no matching memory)'}\n\nQuestion:\n{question}"
                result = build_provider(body.get("provider")).generate(
                    prompt,
                    system=system,
                    model=body.get("model"),
                )
                self._send(
                    HTTPStatus.OK,
                    {
                        "provider": result.provider,
                        "model": result.model,
                        "text": result.text,
                        "memory_hits": hits,
                        "memory_count": len(hits),
                        "session_id": body.get("session_id"),
                    },
                )
                return
            if path == "/v1/conversations/analyze":
                self._send(HTTPStatus.OK, self._analyze_conversation(body))
                return
            if path == "/v1/memory/commit":
                if not self._authorize_cloud_sync():
                    return
                self._send(HTTPStatus.OK, self._commit_memory(body))
                return
            self._send(HTTPStatus.NOT_FOUND, {"error": "not_found", "path": path})
        except (TypeError, ValueError, GoogleOAuthError) as exc:
            self._send(HTTPStatus.BAD_REQUEST, {"error": "bad_request", "detail": str(exc)})
        except ProviderError as exc:
            self._send(HTTPStatus.BAD_GATEWAY, {"error": "provider_error", "detail": str(exc)})
        except Exception as exc:
            self._send(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "internal_error", "detail": str(exc)})

    def _extract_conversation_artifact(self, body: dict[str, Any]):
        conversation = body.get("conversation")
        if isinstance(conversation, list):
            source = json.dumps(conversation, ensure_ascii=False)
        elif isinstance(conversation, str):
            source = conversation
        else:
            raise ValueError("conversation must be a string or message array")
        curator = _load_module("research_os_curator", CURATOR_PATH)
        normalized = curator._normalize_source(source)
        relationships = [curator._parse_relationship(item) for item in body.get("relationships", [])]
        artifact = curator._deterministic_extract(
            normalized,
            str(body.get("title", "Research Session")),
            str(body.get("status", "hypothesis")),
            [str(x) for x in body.get("tags", [])],
            [str(x) for x in body.get("evidence", [])],
            relationships,
            ARTIFACT_DIR,
        )
        return curator, artifact

    def _analyze_conversation(self, body: dict[str, Any]) -> dict[str, Any]:
        curator, artifact = self._extract_conversation_artifact(body)
        return {
            "artifact": curator.asdict(artifact),
            "accepted": artifact.quality_score >= int(body.get("min_quality", 20)),
            "persisted": False,
            "note": "API analysis is preview-only; persistence requires explicit memory commit.",
        }

    def _commit_memory(self, body: dict[str, Any]) -> dict[str, Any]:
        if body.get("confirm") is not True:
            raise ValueError("confirm must be true for explicit memory persistence")
        curator, artifact = self._extract_conversation_artifact(body)
        min_quality = int(body.get("min_quality", 20))
        if artifact.quality_score < min_quality:
            return {
                "artifact": curator.asdict(artifact),
                "accepted": False,
                "persisted": False,
                "reason": "quality_below_threshold",
                "durability": "runtime-ephemeral",
            }
        if artifact.duplicate_of and not bool(body.get("allow_duplicate", False)):
            return {
                "artifact": curator.asdict(artifact),
                "accepted": True,
                "persisted": False,
                "reason": "duplicate",
                "duplicate_of": artifact.duplicate_of,
                "durability": "runtime-ephemeral",
            }
        target = curator._write_artifact(
            ARTIFACT_DIR,
            artifact,
            allow_duplicate=bool(body.get("allow_duplicate", False)),
        )
        curator._update_index(ARTIFACT_DIR)
        return {
            "artifact": curator.asdict(artifact),
            "accepted": True,
            "persisted": True,
            "path": str(target.relative_to(ROOT)) if ROOT in target.parents else str(target),
            "durability": "runtime-ephemeral",
            "note": (
                "Memory is available to Research OS immediately. "
                "Render free-service filesystem is ephemeral; durable Git-backed memory is a later storage phase."
            ),
        }

    @staticmethod
    def _artifact_index() -> list[dict[str, str]]:
        results: list[dict[str, str]] = []
        if not ARTIFACT_DIR.exists():
            return results
        for path in sorted(ARTIFACT_DIR.glob("RES-*.md")):
            text = path.read_text(encoding="utf-8")
            metadata: dict[str, str] = {}
            if text.startswith("---\n"):
                end = text.find("\n---", 4)
                if end > 0:
                    for line in text[4:end].splitlines():
                        if ":" in line:
                            key, value = line.split(":", 1)
                            metadata[key.strip()] = value.strip().strip('"')
            results.append(
                {
                    "artifact_id": metadata.get("artifact_id", path.stem),
                    "title": metadata.get("title", ""),
                    "status": metadata.get("status", ""),
                    "path": str(path.relative_to(ROOT)) if ROOT in path.parents else str(path),
                }
            )
        return results

    def log_request(self, code: int | str = "-", size: int | str = "-") -> None:
        target = self.path
        parsed = urlsplit(target)
        if parsed.path == "/v1/google-workspace/oauth/callback" and parsed.query:
            target = f"{parsed.path}?[REDACTED]"
        self.log_message(
            '"%s %s %s" %s %s',
            self.command,
            target,
            self.request_version,
            str(code),
            str(size),
        )

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
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
