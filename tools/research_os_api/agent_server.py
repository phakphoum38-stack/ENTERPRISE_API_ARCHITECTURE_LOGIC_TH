#!/usr/bin/env python3
"""Research OS HTTP API with Multi-Agent Orchestrator routes.

This module extends the existing ResearchOSHandler without changing its stable
server.py contract. It is safe to validate independently before making it the
primary service entrypoint.
"""

from __future__ import annotations

import argparse
import os
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from agent_orchestrator import ORCHESTRATOR
from server import ResearchOSHandler


class AgentResearchOSHandler(ResearchOSHandler):
    """Adds orchestration endpoints while preserving all existing API routes."""

    _prefix = "/v1/agents/orchestrations"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        path = parsed.path
        if path == self._prefix:
            try:
                query = parse_qs(parsed.query)
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
                self._send(
                    HTTPStatus.BAD_REQUEST,
                    {"error": "bad_request", "detail": str(exc)},
                )
            return

        if path.startswith(self._prefix + "/"):
            relative = path[len(self._prefix) + 1 :].strip("/")
            parts = relative.split("/") if relative else []
            if len(parts) == 2 and parts[1] == "timeline":
                run_id = parts[0]
                try:
                    events = ORCHESTRATOR.timeline(run_id)
                    self._send(
                        HTTPStatus.OK,
                        {"run_id": run_id, "events": events, "count": len(events)},
                    )
                except ValueError as exc:
                    self._send(
                        HTTPStatus.NOT_FOUND,
                        {"error": "orchestration_not_found", "detail": str(exc)},
                    )
                return

            if len(parts) != 1 or not parts[0]:
                self._send(HTTPStatus.NOT_FOUND, {"error": "not_found", "path": path})
                return
            run_id = parts[0]
            try:
                self._send(HTTPStatus.OK, {"run": ORCHESTRATOR.get(run_id)})
            except ValueError as exc:
                self._send(
                    HTTPStatus.NOT_FOUND,
                    {"error": "orchestration_not_found", "detail": str(exc)},
                )
            return

        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
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
                self._send(
                    HTTPStatus.BAD_REQUEST,
                    {"error": "bad_request", "detail": str(exc)},
                )
            return

        if path.startswith(self._prefix + "/"):
            relative = path[len(self._prefix) + 1 :].strip("/")
            parts = relative.split("/") if relative else []
            if len(parts) != 2 or parts[1] not in {"execute", "confirm", "retry", "cancel"}:
                self._send(HTTPStatus.NOT_FOUND, {"error": "not_found", "path": path})
                return
            run_id, action = parts
            try:
                body = self._read_json()
                if action == "execute":
                    run = ORCHESTRATOR.execute(
                        run_id,
                        confirmed=bool(body.get("confirmed", False)),
                    )
                elif action == "confirm":
                    run = ORCHESTRATOR.confirm(run_id)
                elif action == "retry":
                    step_id = body.get("step_id")
                    run = ORCHESTRATOR.retry(
                        run_id,
                        step_id=str(step_id).strip() if step_id else None,
                    )
                else:
                    run = ORCHESTRATOR.cancel(run_id)
                self._send(HTTPStatus.OK, {"run": run})
            except ValueError as exc:
                message = str(exc)
                status = (
                    HTTPStatus.NOT_FOUND
                    if message.startswith("unknown orchestration run:")
                    else HTTPStatus.BAD_REQUEST
                )
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
    parser = argparse.ArgumentParser(
        description="Research OS API with Multi-Agent Orchestrator"
    )
    parser.add_argument(
        "--host",
        default=os.getenv("RESEARCH_OS_API_HOST", "127.0.0.1"),
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("RESEARCH_OS_API_PORT", "8787")),
    )
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
