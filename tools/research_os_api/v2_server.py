#!/usr/bin/env python3
"""Research OS API V2 compatibility, pagination, workspace and intelligence facade.

V2 uses the same V1 runtime/orchestrator owners and the existing Workspace
Knowledge Engine. Only transport contracts are versioned here; state and
business logic remain single-source. Phase 7 adds read-only System Introspection
and planning endpoints; no direct tool execution or permission-grant endpoint is
exposed through this facade.
"""

from __future__ import annotations

import base64
import os
import re
import sys
from collections.abc import Mapping
from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlsplit, urlunsplit

import agent_server
from agent_server import AgentResearchOSHandler
from ai_gateway import gateway_report
from v2_brain_runtime import BRAIN_RUNTIME
from v2_observability import readiness_snapshot
from v2_secret_redactor import sanitize_external
from v2_system_introspection import SystemIntrospection, parse_ready_only

_CURATOR_DIR = Path(__file__).resolve().parents[1] / "research_curator"
if str(_CURATOR_DIR) not in sys.path:
    sys.path.insert(0, str(_CURATOR_DIR))
from workspace_engine import Provenance, WorkspaceKnowledgeEngine  # noqa: E402

_SESSION_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


class V2ResearchOSHandler(AgentResearchOSHandler):
    """Expose V2 contracts while preserving every supported V1 route."""

    _v2_aliases = (
        ("/v2/orchestrations", "/v1/agents/orchestrations"),
        ("/v2/agents", "/v1/agents"),
    )
    _v2_request = False

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        self._v2_request = parsed.path.startswith("/v2/")

        if parsed.path == "/v2/health/readiness":
            payload = readiness_snapshot()
            self._send(
                HTTPStatus.OK if payload["ready"] else HTTPStatus.SERVICE_UNAVAILABLE,
                payload,
            )
            return

        if parsed.path == "/v2/providers":
            self._send(HTTPStatus.OK, {"gateway": gateway_report()})
            return

        if parsed.path == "/v2/orchestrations":
            self._send_v2_orchestration_page(parsed.query)
            return

        if parsed.path == "/v2/workspaces":
            self._send_v2_workspaces()
            return

        if parsed.path.startswith("/v2/workspaces/") and parsed.path.endswith("/knowledge"):
            workspace_id = unquote(parsed.path[len("/v2/workspaces/") : -len("/knowledge")]).strip("/")
            self._send_v2_workspace_knowledge(workspace_id, parsed.query)
            return

        if parsed.path == "/v2/intelligence" or parsed.path.startswith("/v2/intelligence/"):
            self._send_v2_intelligence_get(parsed.path, parsed.query)
            return

        self._rewrite_v2_path()
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        self._v2_request = parsed.path.startswith("/v2/")
        if parsed.path == "/v2/intelligence/plan":
            self._send_v2_intelligence_plan()
            return
        if parsed.path.startswith("/v2/intelligence/"):
            self._send(
                HTTPStatus.NOT_FOUND,
                {"error": "intelligence_route_not_found", "detail": "unknown intelligence POST route"},
            )
            return
        self._rewrite_v2_path()
        super().do_POST()

    @staticmethod
    def _intelligence() -> SystemIntrospection:
        return SystemIntrospection(BRAIN_RUNTIME, agent_server.REGISTRY)

    def _send_v2_intelligence_get(self, path: str, raw_query: str) -> None:
        try:
            query = parse_qs(raw_query)
            capability = self._first(query, "capability")
            permission = self._first(query, "permission")
            ready_only = parse_ready_only(self._first(query, "ready_only"))
            intelligence = self._intelligence()

            if path in {"/v2/intelligence", "/v2/intelligence/"}:
                payload = intelligence.manifest()
            elif path == "/v2/intelligence/capabilities":
                payload = intelligence.capabilities()
            elif path == "/v2/intelligence/agents":
                payload = intelligence.agents(
                    scope=self._first(query, "scope") or "all",
                    capability=capability,
                    permission=permission,
                    ready_only=ready_only,
                )
            elif path == "/v2/intelligence/skills":
                payload = intelligence.skills(
                    capability=capability,
                    permission=permission,
                    ready_only=ready_only,
                )
            elif path == "/v2/intelligence/tools":
                payload = intelligence.tools(
                    capability=capability,
                    permission=permission,
                    ready_only=ready_only,
                )
            elif path == "/v2/intelligence/permissions":
                payload = intelligence.permissions()
            elif path == "/v2/intelligence/architecture":
                payload = intelligence.architecture()
            elif path == "/v2/intelligence/project-state":
                payload = intelligence.project_state()
            elif path == "/v2/intelligence/health":
                payload = intelligence.health()
            else:
                self._send(
                    HTTPStatus.NOT_FOUND,
                    {"error": "intelligence_route_not_found", "detail": f"unknown intelligence route: {path}"},
                )
                return
            self._send(HTTPStatus.OK, payload)
        except (TypeError, ValueError) as exc:
            self._send(
                HTTPStatus.BAD_REQUEST,
                {"error": "invalid_intelligence_query", "detail": str(exc)},
            )

    def _send_v2_intelligence_plan(self) -> None:
        try:
            body = self._read_json()
            objective = str(body.get("objective") or "").strip()
            session_id_raw = str(body.get("session_id") or "").strip()
            context_raw = body.get("context")
            if context_raw is not None and not isinstance(context_raw, Mapping):
                raise ValueError("context must be an object")
            if session_id_raw:
                if not _SESSION_ID_RE.fullmatch(session_id_raw):
                    raise ValueError("session_id must be 1-128 characters using letters, digits, dot, underscore, colon, or hyphen")
                if sanitize_external(session_id_raw) != session_id_raw:
                    raise ValueError("session_id resembles sensitive credential material")

            # Sanitize before BrainRuntime.plan because planning persists the current
            # goal/plan into Working Memory and records an Activity Ledger event.
            # Output-only sanitization would be too late for credential-shaped input.
            safe_objective = sanitize_external(objective)
            safe_context_value = sanitize_external(dict(context_raw or {}))
            if not isinstance(safe_objective, str):
                raise ValueError("objective must resolve to text")
            if not isinstance(safe_context_value, Mapping):
                raise ValueError("context must resolve to an object")

            payload = self._intelligence().plan(
                safe_objective,
                session_id=session_id_raw or None,
                context=dict(safe_context_value),
            )
            self._send(HTTPStatus.OK, payload)
        except (TypeError, ValueError) as exc:
            self._send(
                HTTPStatus.BAD_REQUEST,
                {"error": "invalid_intelligence_plan", "detail": str(exc)},
            )

    def _workspace_engine(self) -> WorkspaceKnowledgeEngine:
        data_dir = os.environ.get("RESEARCH_OS_DATA_DIR") or str(Path.home() / "ResearchOSData")
        return WorkspaceKnowledgeEngine(data_dir)

    def _send_v2_workspaces(self) -> None:
        try:
            workspaces = self._workspace_engine().list_workspaces()
            self._send(
                HTTPStatus.OK,
                {"workspaces": workspaces, "count": len(workspaces)},
            )
        except (OSError, RuntimeError, ValueError) as exc:
            self._send(
                HTTPStatus.SERVICE_UNAVAILABLE,
                {"error": "workspace_index_unavailable", "detail": str(exc)},
            )

    def _send_v2_workspace_knowledge(self, workspace_id: str, raw_query: str) -> None:
        if not workspace_id:
            self._send(
                HTTPStatus.BAD_REQUEST,
                {"error": "workspace_id_required", "detail": "workspace_id is required"},
            )
            return
        try:
            query = parse_qs(raw_query)
            page_size = int(self._first(query, "page_size") or "25")
            if page_size < 1 or page_size > 100:
                raise ValueError("page_size must be between 1 and 100")
            offset = self._decode_cursor(self._first(query, "cursor"))
            text_query = self._first(query, "q") or ""
            kinds_raw = self._first(query, "kinds") or ""
            kinds = [item.strip() for item in kinds_raw.split(",") if item.strip()]
            engine = self._workspace_engine()
            records = engine.search(
                workspace_id,
                text_query,
                kinds=kinds,
                limit=200,
            )
            items = records[offset : offset + page_size]
            next_offset = offset + len(items)
            next_cursor = self._encode_cursor(next_offset) if next_offset < len(records) else None
            self._send(
                HTTPStatus.OK,
                {
                    "workspace_id": workspace_id,
                    "items": items,
                    "page": {
                        "page_size": page_size,
                        "returned": len(items),
                        "next_cursor": next_cursor,
                    },
                    "filters": {"q": text_query, "kinds": kinds},
                },
            )
        except ValueError as exc:
            message = str(exc)
            status = HTTPStatus.NOT_FOUND if message.startswith("unknown workspace:") else HTTPStatus.BAD_REQUEST
            code = "workspace_not_found" if status == HTTPStatus.NOT_FOUND else "invalid_workspace_query"
            self._send(status, {"error": code, "detail": message})
        except (OSError, RuntimeError) as exc:
            self._send(
                HTTPStatus.SERVICE_UNAVAILABLE,
                {"error": "workspace_index_unavailable", "detail": str(exc)},
            )

    def _send_v2_orchestration_page(self, raw_query: str) -> None:
        try:
            query = parse_qs(raw_query)
            page_size = int(self._first(query, "page_size") or "50")
            if page_size < 1 or page_size > 100:
                raise ValueError("page_size must be between 1 and 100")
            offset = self._decode_cursor(self._first(query, "cursor"))
            all_runs = agent_server.ORCHESTRATOR.list(
                status=self._first(query, "status"),
                query=self._first(query, "q"),
                agent=self._first(query, "agent"),
                limit=200,
            )
            items = all_runs[offset : offset + page_size]
            next_offset = offset + len(items)
            next_cursor = (
                self._encode_cursor(next_offset) if next_offset < len(all_runs) else None
            )
            self._send(
                HTTPStatus.OK,
                {
                    "items": items,
                    "page": {
                        "page_size": page_size,
                        "returned": len(items),
                        "next_cursor": next_cursor,
                    },
                    "filters": {
                        "status": self._first(query, "status"),
                        "q": self._first(query, "q"),
                        "agent": self._first(query, "agent"),
                    },
                },
            )
        except (TypeError, ValueError) as exc:
            self._send(
                HTTPStatus.BAD_REQUEST,
                {"error": "invalid_pagination", "detail": str(exc)},
            )

    def _send(self, status: HTTPStatus | int, payload: dict[str, Any]) -> None:
        status_code = int(status)
        if self._v2_request:
            if status_code >= 400:
                raw_code = payload.get("error")
                code = raw_code if isinstance(raw_code, str) else f"http_{status_code}"
                message = str(payload.get("detail") or payload.get("message") or code)
                payload = {
                    "api_version": "v2",
                    "error": {
                        "code": code,
                        "message": message,
                        "status": status_code,
                    },
                }
            else:
                payload = {"api_version": "v2", **payload}
        super()._send(status, payload)

    def _rewrite_v2_path(self) -> None:
        parsed = urlsplit(self.path)
        rewritten = parsed.path
        for source, target in self._v2_aliases:
            if rewritten == source or rewritten.startswith(source + "/"):
                rewritten = target + rewritten[len(source) :]
                break
        if rewritten == parsed.path:
            return
        self.path = urlunsplit(
            (parsed.scheme, parsed.netloc, rewritten, parsed.query, parsed.fragment)
        )

    @staticmethod
    def _first(query: dict[str, list[str]], key: str) -> str | None:
        values = query.get(key)
        if not values:
            return None
        value = values[0].strip()
        return value or None

    @staticmethod
    def _encode_cursor(offset: int) -> str:
        return base64.urlsafe_b64encode(str(offset).encode("ascii")).decode("ascii").rstrip("=")

    @staticmethod
    def _decode_cursor(value: str | None) -> int:
        if not value:
            return 0
        try:
            padded = value + "=" * (-len(value) % 4)
            decoded = base64.urlsafe_b64decode(padded.encode("ascii")).decode("ascii")
            offset = int(decoded)
        except (ValueError, UnicodeError) as exc:
            raise ValueError("cursor is invalid") from exc
        if offset < 0:
            raise ValueError("cursor is invalid")
        return offset


__all__ = ["Provenance", "V2ResearchOSHandler", "WorkspaceKnowledgeEngine"]
