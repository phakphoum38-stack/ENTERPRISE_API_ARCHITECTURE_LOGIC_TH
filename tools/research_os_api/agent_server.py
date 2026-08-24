#!/usr/bin/env python3
"""Research OS HTTP API with Multi-Agent Orchestrator routes."""

from __future__ import annotations

import argparse
import os
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from agent_orchestrator import ORCHESTRATOR
from agent_platform import REGISTRY
from api_auth import require_session
from file_acl import ACLAuthorizationError, FileACLStore
from google_identity import GoogleIdentityBroker
from server import ResearchOSHandler


class AgentResearchOSHandler(ResearchOSHandler):
    """Adds agent discovery, orchestration and resource ACL routes."""

    _agents_prefix = "/v1/agents"
    _prefix = "/v1/agents/orchestrations"
    _acl_prefix = "/v1/files/acl"
    _protected_prefixes = (_agents_prefix, _acl_prefix)

    @staticmethod
    def _acl_store() -> FileACLStore:
        root = GoogleIdentityBroker().root
        return FileACLStore(root / "file_acl.json")

    def _require_principal(self) -> dict[str, object] | None:
        """Resolve the trusted Research OS session before serving protected routes."""
        try:
            return require_session(dict(self.headers.items()))
        except ValueError as exc:
            self._send(
                HTTPStatus.UNAUTHORIZED,
                {"error": "authentication_required", "detail": str(exc)},
            )
        except RuntimeError as exc:
            self._send(
                HTTPStatus.SERVICE_UNAVAILABLE,
                {"error": "authentication_unavailable", "detail": str(exc)},
            )
        return None

    def _signed_in_email(self) -> str:
        principal = self._require_principal()
        if not principal:
            raise ACLAuthorizationError("Research OS session is required")
        email = str(principal.get("email") or "").strip()
        if not email:
            raise ACLAuthorizationError("Research OS session identity is incomplete")
        return email

    def _is_protected_path(self, path: str) -> bool:
        return any(path == prefix or path.startswith(prefix + "/") for prefix in self._protected_prefixes)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if self._is_protected_path(path) and not self._require_principal():
            return

        if path == self._agents_prefix:
            agents = REGISTRY.list()
            self._send(HTTPStatus.OK, {"agents": agents, "count": len(agents)})
            return

        if path == self._agents_prefix + "/readiness":
            self._send(HTTPStatus.OK, REGISTRY.readiness())
            return

        if path == self._agents_prefix + "/discover":
            ready_raw = self._first_query_value(query, "ready_only")
            ready_only = ready_raw is None or ready_raw.casefold() not in {"0", "false", "no"}
            agents = REGISTRY.discover(
                capability=self._first_query_value(query, "capability"),
                permission=self._first_query_value(query, "permission"),
                ready_only=ready_only,
            )
            self._send(
                HTTPStatus.OK,
                {
                    "agents": agents,
                    "count": len(agents),
                    "filters": {
                        "capability": self._first_query_value(query, "capability"),
                        "permission": self._first_query_value(query, "permission"),
                        "ready_only": ready_only,
                    },
                },
            )
            return

        if path.startswith(self._acl_prefix + "/"):
            resource_id = path[len(self._acl_prefix) + 1:].strip("/")
            try:
                actor = self._signed_in_email()
                store = self._acl_store()
                if resource_id == "":
                    self._send(HTTPStatus.NOT_FOUND, {"error": "not_found", "path": path})
                    return
                action = self._first_query_value(query, "action") or "read"
                allowed = store.authorize(resource_id, actor, action)
                self._send(HTTPStatus.OK, {"resource_id": resource_id, "actor": actor, "action": action, "allowed": allowed})
            except ACLAuthorizationError as exc:
                self._send(HTTPStatus.FORBIDDEN, {"error": "acl_denied", "detail": str(exc)})
            return

        if path == self._acl_prefix:
            try:
                actor = self._signed_in_email()
                resource_id = self._first_query_value(query, "resource")
                if not resource_id:
                    raise ValueError("resource is required")
                self._send(HTTPStatus.OK, {"resource_id": resource_id, "actor": actor, "acl": self._acl_store().snapshot(resource_id)})
            except ACLAuthorizationError as exc:
                self._send(HTTPStatus.FORBIDDEN, {"error": "acl_denied", "detail": str(exc)})
            except ValueError as exc:
                self._send(HTTPStatus.BAD_REQUEST, {"error": "bad_request", "detail": str(exc)})
            return

        if path == self._prefix:
            try:
                limit_raw = self._first_query_value(query, "limit")
                limit = int(limit_raw) if limit_raw else None
                runs = ORCHESTRATOR.list(
                    status=self._first_query_value(query, "status"),
                    query=self._first_query_value(query, "q"),
                    agent=self._first_query_value(query, "agent"),
                    limit=limit,
                )
                self._send(
                    HTTPStatus.OK,
                    {
                        "runs": runs,
                        "count": len(runs),
                        "filters": {
                            "status": self._first_query_value(query, "status"),
                            "q": self._first_query_value(query, "q"),
                            "agent": self._first_query_value(query, "agent"),
                            "limit": limit,
                        },
                    },
                )
            except (TypeError, ValueError) as exc:
                self._send(HTTPStatus.BAD_REQUEST, {"error": "bad_request", "detail": str(exc)})
            return

        if path.startswith(self._prefix + "/"):
            relative = path[len(self._prefix) + 1 :].strip("/")
            parts = relative.split("/") if relative else []
            if len(parts) == 2 and parts[1] == "timeline":
                run_id = parts[0]
                try:
                    events = ORCHESTRATOR.timeline(run_id)
                    self._send(HTTPStatus.OK, {"run_id": run_id, "events": events, "count": len(events)})
                except ValueError as exc:
                    self._send(HTTPStatus.NOT_FOUND, {"error": "orchestration_not_found", "detail": str(exc)})
                return

            if len(parts) != 1 or not parts[0]:
                self._send(HTTPStatus.NOT_FOUND, {"error": "not_found", "path": path})
                return
            run_id = parts[0]
            try:
                self._send(HTTPStatus.OK, {"run": ORCHESTRATOR.get(run_id)})
            except ValueError as exc:
                self._send(HTTPStatus.NOT_FOUND, {"error": "orchestration_not_found", "detail": str(exc)})
            return

        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path

        if self._is_protected_path(path) and not self._require_principal():
            return

        if path == self._acl_prefix:
            try:
                body = self._read_json()
                resource_id = str(body.get("resource_id", "")).strip()
                if not resource_id:
                    raise ValueError("resource_id is required")
                actor = self._signed_in_email()
                acl = self._acl_store().create(resource_id, actor)
                self._send(HTTPStatus.CREATED, {"resource_id": resource_id, "actor": actor, "acl": acl})
            except ACLAuthorizationError as exc:
                self._send(HTTPStatus.FORBIDDEN, {"error": "acl_denied", "detail": str(exc)})
            except ValueError as exc:
                self._send(HTTPStatus.BAD_REQUEST, {"error": "bad_request", "detail": str(exc)})
            return

        if path.startswith(self._acl_prefix + "/"):
            relative = path[len(self._acl_prefix) + 1:].strip("/")
            parts = relative.split("/") if relative else []
            if len(parts) != 2 or parts[1] not in {"share", "revoke", "transfer"}:
                self._send(HTTPStatus.NOT_FOUND, {"error": "not_found", "path": path})
                return
            resource_id, action = parts
            try:
                body = self._read_json()
                actor = self._signed_in_email()
                store = self._acl_store()
                target = str(body.get("email", "")).strip()
                if not target:
                    raise ValueError("email is required")
                if action == "share":
                    acl = store.share(resource_id, actor, target)
                elif action == "revoke":
                    acl = store.revoke(resource_id, actor, target)
                else:
                    acl = store.transfer(resource_id, actor, target)
                self._send(HTTPStatus.OK, {"resource_id": resource_id, "actor": actor, "action": action, "acl": acl})
            except ACLAuthorizationError as exc:
                self._send(HTTPStatus.FORBIDDEN, {"error": "acl_denied", "detail": str(exc)})
            except ValueError as exc:
                self._send(HTTPStatus.BAD_REQUEST, {"error": "bad_request", "detail": str(exc)})
            return

        if path == self._prefix:
            try:
                body = self._read_json()
                steps = body.get("steps")
                if not isinstance(steps, list):
                    raise ValueError("steps must be an array")
                run = ORCHESTRATOR.create_run(
                    str(body.get("objective", "")),
                    [dict(item) for item in steps if isinstance(item, dict)],
                )
                if len(run["steps"]) != len(steps):
                    raise ValueError("every step must be an object")
                self._send(HTTPStatus.CREATED, {"run": run})
            except (TypeError, ValueError) as exc:
                self._send(HTTPStatus.BAD_REQUEST, {"error": "bad_request", "detail": str(exc)})
            return

        if path.startswith(self._prefix + "/"):
            relative = path[len(self._prefix) + 1:].strip("/")
            parts = relative.split("/") if relative else []
            if len(parts) != 2 or parts[1] not in {"execute", "confirm", "retry", "cancel"}:
                self._send(HTTPStatus.NOT_FOUND, {"error": "not_found", "path": path})
                return
            run_id, action = parts
            try:
                body = self._read_json()
                if action == "execute":
                    run = ORCHESTRATOR.execute(run_id, confirmed=bool(body.get("confirmed", False)))
                elif action == "confirm":
                    run = ORCHESTRATOR.confirm(run_id)
                elif action == "retry":
                    step_id = body.get("step_id")
                    run = ORCHESTRATOR.retry(run_id, step_id=str(step_id).strip() if step_id else None)
                else:
                    run = ORCHESTRATOR.cancel(run_id)
                self._send(HTTPStatus.OK, {"run": run})
            except ValueError as exc:
                message = str(exc)
                status = HTTPStatus.NOT_FOUND if message.startswith("unknown orchestration run:") else HTTPStatus.BAD_REQUEST
                self._send(status, {"error": "orchestration_error", "detail": message})
            return

        super().do_POST()

    @staticmethod
    def _first_query_value(query: dict[str, list[str]], key: str) -> str | None:
        values = query.get(key)
        if not values:
            return None
        value = values[0].strip()
        return value or None


def main() -> int:
    parser = argparse.ArgumentParser(description="Research OS API with Multi-Agent Orchestrator")
    parser.add_argument("--host", default=os.getenv("RESEARCH_OS_API_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("RESEARCH_OS_API_PORT", "8787")))
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), AgentResearchOSHandler)
    print(f"Research OS Agent API listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
