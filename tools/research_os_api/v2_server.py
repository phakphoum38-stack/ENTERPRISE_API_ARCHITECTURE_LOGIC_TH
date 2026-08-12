#!/usr/bin/env python3
"""Research OS API V2 compatibility, pagination, workspace and readiness facade.

V2 uses the same V1 runtime/orchestrator owners and the existing Workspace
Knowledge Engine. Only transport contracts are versioned here; state and
business logic remain single-source.
"""

from __future__ import annotations

import base64
import os
import sys
from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlsplit, urlunsplit

import agent_server
from agent_server import AgentResearchOSHandler
from brain_skills import BRAIN
from providers import (
    ProviderError,
    build_search_provider,
    provider_credential_status,
)
from v2_observability import readiness_snapshot

_CURATOR_DIR = Path(__file__).resolve().parents[1] / "research_curator"
if str(_CURATOR_DIR) not in sys.path:
    sys.path.insert(0, str(_CURATOR_DIR))
from workspace_engine import Provenance, WorkspaceKnowledgeEngine  # noqa: E402


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

        if parsed.path == "/v2/master":
            capacity = BRAIN.capacity_snapshot()
            self._send(
                HTTPStatus.OK,
                {
                    "master": {
                        "contract": "unified-master-orchestrator-v3",
                        "architecture": capacity["architecture"],
                        "provider_mode": "local_or_configured_provider",
                        "capacity": capacity,
                        "state_owners": {
                            "orchestrator": "agent_server.ORCHESTRATOR",
                            "brain": "brain_skills.BRAIN",
                        },
                    }
                },
            )
            return

        if parsed.path == "/v2/brain/skills":
            self._send(HTTPStatus.OK, {"brain": BRAIN.catalog()})
            return

        if parsed.path == "/v2/brain/capacity":
            self._send(HTTPStatus.OK, {"capacity": BRAIN.capacity_snapshot()})
            return

        if parsed.path == "/v2/brain/providers":
            self._send(
                HTTPStatus.OK,
                {"providers": provider_credential_status()},
            )
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

        self._rewrite_v2_path()
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        self._v2_request = parsed.path.startswith("/v2/")

        if parsed.path == "/v2/brain/plans":
            try:
                body = self._read_json()
                plan = BRAIN.plan(
                    str(body.get("objective") or ""),
                    complexity_level=self._optional_int(
                        body.get("complexity_level"),
                        "complexity_level",
                    ),
                    requested_workers=self._optional_int(
                        body.get("requested_workers"),
                        "requested_workers",
                    ),
                    budget_workers=self._optional_int(
                        body.get("budget_workers"),
                        "budget_workers",
                    ),
                    ready_workers=self._optional_int(
                        body.get("ready_workers"),
                        "ready_workers",
                    ),
                )
                self._send(HTTPStatus.CREATED, {"plan": plan})
            except (TypeError, ValueError) as exc:
                self._send(
                    HTTPStatus.BAD_REQUEST,
                    {"error": "invalid_brain_plan", "detail": str(exc)},
                )
            return

        if parsed.path == "/v2/brain/search":
            self._send_v2_brain_search()
            return

        self._rewrite_v2_path()
        super().do_POST()

    def _send_v2_brain_search(self) -> None:
        try:
            body = self._read_json()
            query = str(body.get("query") or "").strip()
            if not query:
                raise ValueError("query is required")
            if len(query) > 20000:
                raise ValueError("query must not exceed 20000 characters")

            plan = BRAIN.plan(
                query,
                complexity_level=int(body.get("complexity_level", 3)),
                requested_workers=self._optional_int(
                    body.get("requested_workers"),
                    "requested_workers",
                ),
                budget_workers=self._optional_int(
                    body.get("budget_workers"),
                    "budget_workers",
                ),
                ready_workers=self._optional_int(
                    body.get("ready_workers"),
                    "ready_workers",
                ),
            )
            provider_name = str(body.get("provider") or "").strip() or None
            model = str(body.get("model") or "").strip() or None
            provider = build_search_provider(provider_name)
            result = provider.search(
                query,
                system=BRAIN.research_instructions(plan),
                model=model,
            )
            self._send(
                HTTPStatus.OK,
                {
                    "result": {
                        "provider": result.provider,
                        "model": result.model,
                        "text": result.text,
                        "sources": list(result.sources),
                    },
                    "brain_plan": plan,
                },
            )
        except (TypeError, ValueError) as exc:
            self._send(
                HTTPStatus.BAD_REQUEST,
                {"error": "invalid_brain_search", "detail": str(exc)},
            )
        except ProviderError as exc:
            self._send(
                HTTPStatus.SERVICE_UNAVAILABLE,
                {"error": "brain_provider_unavailable", "detail": str(exc)},
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
    def _optional_int(value: Any, name: str) -> int | None:
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name} must be an integer") from exc

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