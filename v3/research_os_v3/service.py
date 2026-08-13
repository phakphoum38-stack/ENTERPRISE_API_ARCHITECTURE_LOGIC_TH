from __future__ import annotations

import ipaddress
import json
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .contracts import health_contract, master_contract, providers_contract
from .models import Workload
from .orchestrator import UnifiedMasterOrchestrator
from .providers import CompletionRequest
from .storage import DataLayout
from .user_context import UserContext

USER_HEADER = "X-Research-OS-User"
PROFILE_HEADER = "X-Research-OS-Profile"
_MAX_REQUEST_BODY = 1024 * 1024
_CHAT_INPUT_FIELDS = ("message", "text", "prompt", "question")


class V3LocalService:
    """Loopback-only HTTP service exposing stable V3 contracts."""

    def __init__(
        self,
        *,
        host: str = "127.0.0.1",
        port: int = 8788,
        orchestrator: UnifiedMasterOrchestrator | None = None,
        audit_path: Path | None = None,
        data_layout: DataLayout | None = None,
    ) -> None:
        address = ipaddress.ip_address(host)
        if not address.is_loopback:
            raise ValueError("V3 local service must bind to a loopback address")
        self.host = host
        self.port = port
        self.orchestrator = orchestrator or UnifiedMasterOrchestrator()
        self.audit_path = audit_path
        self.data_layout = (data_layout or DataLayout.from_environment()).ensure()
        self._server: ThreadingHTTPServer | None = None

    def build_server(self) -> ThreadingHTTPServer:
        orchestrator = self.orchestrator
        data_layout = self.data_layout
        audit_path = self.audit_path
        audit_lock = threading.Lock()
        if audit_path is not None:
            audit_path.parent.mkdir(parents=True, exist_ok=True)

        def write_audit(method: str, path: str, status: int) -> None:
            if audit_path is None:
                return
            record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "method": method,
                "path": path,
                "status": status,
            }
            line = json.dumps(record, sort_keys=True) + "\n"
            with audit_lock:
                with audit_path.open("a", encoding="utf-8") as stream:
                    stream.write(line)

        class Handler(BaseHTTPRequestHandler):
            server_version = "ResearchOSV3Clean/1"

            def log_message(self, format: str, *args: object) -> None:
                return

            def _write_json(self, status: int, payload: dict[str, object]) -> None:
                body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode(
                    "utf-8"
                )
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                write_audit(self.command, urlparse(self.path).path, status)
                self.wfile.write(body)

            def _required_user_context(self) -> UserContext | None:
                user_id = self.headers.get(USER_HEADER)
                if not user_id:
                    self._write_json(
                        400,
                        {
                            "error": "missing user context",
                            "required_header": USER_HEADER,
                        },
                    )
                    return None
                profile_id = self.headers.get(PROFILE_HEADER, "default")
                try:
                    return UserContext(user_id=user_id, profile_id=profile_id)
                except ValueError as exc:
                    self._write_json(
                        400,
                        {"error": "invalid user context", "detail": str(exc)},
                    )
                    return None

            def _read_json_object(self) -> dict[str, object]:
                raw_length = self.headers.get("Content-Length", "").strip()
                if not raw_length:
                    raise ValueError("request body is required")
                try:
                    length = int(raw_length)
                except ValueError as exc:
                    raise ValueError("invalid Content-Length") from exc
                if length <= 0:
                    raise ValueError("request body is required")
                if length > _MAX_REQUEST_BODY:
                    raise ValueError("request body exceeds 1 MiB limit")
                try:
                    decoded = json.loads(self.rfile.read(length).decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise ValueError("request body must be valid JSON") from exc
                if not isinstance(decoded, dict):
                    raise ValueError("request body must be a JSON object")
                return decoded

            def _chat_input(self, payload: dict[str, object]) -> tuple[str, str]:
                for field in _CHAT_INPUT_FIELDS:
                    value = payload.get(field)
                    if isinstance(value, str) and value.strip():
                        return value.strip(), field
                raise ValueError(
                    "one of message, text, prompt, or question is required"
                )

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
                if parsed.path == "/v3/user":
                    context = self._required_user_context()
                    if context is None:
                        return
                    user_layout = data_layout.for_user(context).ensure()
                    self._write_json(
                        200,
                        {
                            "user_id": context.user_id,
                            "profile_id": context.profile_id,
                            "scope": f"users/{context.user_id}/profiles/{context.profile_id}",
                            "isolated": True,
                            "directories": sorted(user_layout.directories()),
                        },
                    )
                    return
                self._write_json(404, {"error": "not found"})

            def do_POST(self) -> None:  # noqa: N802 - stdlib handler contract
                parsed = urlparse(self.path)
                if parsed.path != "/v3/chat":
                    self._write_json(404, {"error": "not found"})
                    return

                context = self._required_user_context()
                if context is None:
                    return

                try:
                    payload = self._read_json_object()
                    message, input_field = self._chat_input(payload)
                    workload = Workload(
                        estimated_leaf_tasks=int(payload.get("tasks", 1)),
                        risk=int(payload.get("risk", 1)),
                        parallelism=int(payload.get("parallelism", 1)),
                    )
                except (TypeError, ValueError) as exc:
                    self._write_json(
                        400,
                        {
                            "error": "invalid request body",
                            "detail": str(exc),
                            "accepted_input_fields": list(_CHAT_INPUT_FIELDS),
                        },
                    )
                    return

                raw_provider = payload.get("provider")
                preferred_provider = (
                    raw_provider.strip()
                    if isinstance(raw_provider, str) and raw_provider.strip()
                    else None
                )
                if preferred_provider == "auto":
                    preferred_provider = None

                raw_system = payload.get("system_prompt", payload.get("system"))
                system_prompt = (
                    raw_system.strip()
                    if isinstance(raw_system, str) and raw_system.strip()
                    else None
                )
                session_id = str(payload.get("session_id", "default")).strip() or "default"
                mode = str(payload.get("mode", "answer")).strip() or "answer"

                try:
                    decision = orchestrator.decide(workload)
                    completion = orchestrator.providers.complete(
                        CompletionRequest(
                            prompt=message,
                            system_prompt=system_prompt,
                        ),
                        preferred=preferred_provider,
                    )
                except KeyError:
                    self._write_json(
                        400,
                        {
                            "error": "invalid provider",
                            "provider": preferred_provider or "auto",
                        },
                    )
                    return
                except RuntimeError as exc:
                    self._write_json(
                        502,
                        {
                            "error": "provider unavailable",
                            "detail": str(exc),
                        },
                    )
                    return

                data_layout.for_user(context).ensure()
                self._write_json(
                    200,
                    {
                        "contract": "research-os-v3-chat-v1",
                        "text": completion.text,
                        "answer": completion.text,
                        "provider": completion.provider,
                        "model": completion.model,
                        "user_id": context.user_id,
                        "profile_id": context.profile_id,
                        "scope": f"users/{context.user_id}/profiles/{context.profile_id}",
                        "session_id": session_id,
                        "mode": mode,
                        "input_field": input_field,
                        "memory_hits": [],
                        "memory_count": 0,
                        "decision": {
                            "scale": decision.profile.tier.value,
                            "maximum_leaf_capacity": decision.profile.capacity,
                            "demand": decision.demand,
                            "reason": decision.reason,
                            "orchestrated_provider": decision.provider,
                        },
                    },
                )

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
