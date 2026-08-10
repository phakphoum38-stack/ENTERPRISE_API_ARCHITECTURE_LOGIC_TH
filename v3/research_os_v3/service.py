from __future__ import annotations

import ipaddress
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .contracts import health_contract, master_contract, providers_contract
from .models import Workload
from .orchestrator import UnifiedMasterOrchestrator


class V3LocalService:
    """Loopback-only HTTP service exposing stable V3 contracts."""

    def __init__(
        self,
        *,
        host: str = "127.0.0.1",
        port: int = 8788,
        orchestrator: UnifiedMasterOrchestrator | None = None,
    ) -> None:
        address = ipaddress.ip_address(host)
        if not address.is_loopback:
            raise ValueError("V3 local service must bind to a loopback address")
        self.host = host
        self.port = port
        self.orchestrator = orchestrator or UnifiedMasterOrchestrator()
        self._server: ThreadingHTTPServer | None = None

    def build_server(self) -> ThreadingHTTPServer:
        orchestrator = self.orchestrator

        class Handler(BaseHTTPRequestHandler):
            server_version = "ResearchOSV3Clean/1"

            def log_message(self, format: str, *args: object) -> None:
                return

            def _write_json(self, status: int, payload: dict[str, object]) -> None:
                body = json.dumps(payload, sort_keys=True).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self) -> None:  # noqa: N802 - stdlib handler contract
                parsed = urlparse(self.path)
                if parsed.path == "/health":
                    self._write_json(200, health_contract())
                    return
                if parsed.path == "/v3/providers":
                    self._write_json(200, providers_contract(orchestrator.providers))
                    return
                if parsed.path == "/v3/master":
                    query = parse_qs(parsed.query)
                    try:
                        workload = Workload(
                            estimated_leaf_tasks=int(query.get("tasks", ["1"])[0]),
                            risk=int(query.get("risk", ["1"])[0]),
                            parallelism=int(query.get("parallelism", ["1"])[0]),
                        )
                    except ValueError:
                        self._write_json(400, {"error": "invalid workload parameters"})
                        return
                    decision = orchestrator.decide(workload)
                    self._write_json(200, master_contract(decision))
                    return
                self._write_json(404, {"error": "not found"})

        server = ThreadingHTTPServer((self.host, self.port), Handler)
        self._server = server
        return server

    def serve_forever(self) -> None:
        server = self._server or self.build_server()
        server.serve_forever(poll_interval=0.1)

    def shutdown(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
