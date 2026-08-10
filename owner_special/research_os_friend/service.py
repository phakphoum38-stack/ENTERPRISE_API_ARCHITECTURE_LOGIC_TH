from __future__ import annotations

import json
import os
import re
import threading
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .models import FriendRequest
from .runtime import FriendRuntime

OWNER_HEADER = "X-Research-OS-Owner"
PROFILE_HEADER = "X-Research-OS-Profile"
SESSION_HEADER = "X-Research-OS-Session"
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def _safe_scope(value: str, field: str) -> str:
    candidate = value.strip()
    if candidate in {"", ".", ".."} or not _ID_RE.fullmatch(candidate):
        raise ValueError(f"invalid {field}")
    return candidate


def default_owner_data_root() -> Path:
    configured = os.environ.get("RESEARCH_OS_OWNER_DATA_ROOT", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    program_data = os.environ.get("PROGRAMDATA", "").strip()
    if os.name == "nt" and program_data:
        return (Path(program_data) / "ResearchOSOwnerSpecial").resolve()
    return (Path.home() / ".research_os_owner_special").resolve()


class OwnerFriendService:
    """Loopback-only HTTP boundary for the Owner Special Friend runtime."""

    def __init__(
        self,
        *,
        owner_id: str,
        host: str = "127.0.0.1",
        port: int = 8790,
        data_root: Path | None = None,
        repository_root: Path | None = None,
        audit_path: Path | None = None,
    ) -> None:
        if host != "127.0.0.1":
            raise ValueError("Owner Friend Service must bind to 127.0.0.1")
        self.host = host
        self.data_root = Path(data_root or default_owner_data_root()).resolve()
        self.audit_path = Path(audit_path).resolve() if audit_path is not None else None
        self.runtime = FriendRuntime.create_owner_special(
            owner_id,
            data_root=self.data_root,
            repository_root=repository_root,
        )
        handler = self._make_handler()
        self.httpd = ThreadingHTTPServer((host, port), handler)
        self.port = int(self.httpd.server_address[1])
        self._thread: threading.Thread | None = None

    def _make_handler(self):
        service = self

        class Handler(BaseHTTPRequestHandler):
            server_version = "ResearchOSOwnerFriend/1.2"

            def log_message(self, format: str, *args: object) -> None:
                return

            def _audit(self, status: int) -> None:
                if service.audit_path is None:
                    return
                service.audit_path.parent.mkdir(parents=True, exist_ok=True)
                record = {
                    "method": self.command,
                    "path": urlparse(self.path).path,
                    "status": int(status),
                }
                with service.audit_path.open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(record, sort_keys=True) + "\n")

            def _send_json(self, status: int, payload: dict[str, object]) -> None:
                body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
                self._audit(status)
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _scope(self) -> tuple[str, str, str]:
                claimed_owner = self.headers.get(OWNER_HEADER, "").strip()
                if not claimed_owner or not service.runtime.owner.matches(claimed_owner):
                    raise PermissionError("owner identity rejected")
                profile_id = _safe_scope(self.headers.get(PROFILE_HEADER, "default"), "profile_id")
                session_id = _safe_scope(self.headers.get(SESSION_HEADER, "default"), "session_id")
                return claimed_owner, profile_id, session_id

            def _read_payload(self) -> dict[str, object]:
                length = int(self.headers.get("Content-Length", "0") or "0")
                if length <= 0 or length > 1024 * 1024:
                    raise ValueError("request body is required")
                decoded = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(decoded, dict):
                    raise ValueError("request body must be a JSON object")
                return decoded

            def do_GET(self) -> None:
                path = urlparse(self.path).path
                try:
                    if path == "/owner/health":
                        self._send_json(200, {
                            "status": "ok",
                            "edition": "owner-special",
                            "version": "1.2.0-owner",
                            "loopback_only": True,
                        })
                        return
                    owner_id, profile_id, session_id = self._scope()
                    if path == "/owner/status":
                        architecture = service.runtime.architecture()
                        architecture.update({
                            "service": "owner-friend",
                            "version": "1.2.0-owner",
                            "profile_id": profile_id,
                            "session_id": session_id,
                        })
                        self._send_json(200, architecture)
                        return
                    if path == "/owner/memory":
                        items = service.runtime.orchestrator.memory.recall(
                            owner_id=owner_id,
                            profile_id=profile_id,
                            session_id=session_id,
                        )
                        self._send_json(200, {
                            "owner_id": owner_id,
                            "profile_id": profile_id,
                            "session_id": session_id,
                            "count": len(items),
                            "items": [asdict(item) for item in items],
                        })
                        return
                    self._send_json(404, {"error": "not_found"})
                except PermissionError as exc:
                    self._send_json(403, {"error": "forbidden", "message": str(exc)})
                except (ValueError, KeyError, json.JSONDecodeError) as exc:
                    self._send_json(400, {"error": "bad_request", "message": str(exc)})
                except Exception as exc:
                    self._send_json(500, {"error": "internal_error", "type": type(exc).__name__})

            def do_POST(self) -> None:
                path = urlparse(self.path).path
                try:
                    if path != "/owner/chat":
                        self._send_json(404, {"error": "not_found"})
                        return
                    owner_id, profile_id, session_id = self._scope()
                    payload = self._read_payload()
                    text = str(payload.get("text", "")).strip()
                    if not text:
                        raise ValueError("text is required")
                    skills = tuple(str(item) for item in payload.get("requested_skills", []) or [])
                    tools = tuple(str(item) for item in payload.get("requested_tools", []) or [])
                    request = FriendRequest(
                        owner_id=owner_id,
                        profile_id=profile_id,
                        session_id=session_id,
                        text=text,
                        complexity=int(payload.get("complexity", 1)),
                        risk=int(payload.get("risk", 1)),
                        parallelism=int(payload.get("parallelism", 1)),
                        requested_skills=skills,
                        requested_tools=tools,
                    )
                    response = service.runtime.ask(request)
                    factory = service.runtime.bridge.factory_plan(response.decision.scale.value)
                    self._send_json(200, {
                        "text": response.text,
                        "provider": response.provider,
                        "memory_items": response.memory_items,
                        "evidence_id": response.evidence_id,
                        "decision": {
                            "scale": response.decision.scale.value,
                            "capacity": response.decision.maximum_leaf_capacity,
                            "plan": list(response.decision.plan),
                            "skills": list(response.decision.selected_skills),
                            "tools": list(response.decision.selected_tools),
                            "summary": response.decision.summary,
                        },
                        "factory": factory,
                        "metadata": response.metadata,
                    })
                except PermissionError as exc:
                    self._send_json(403, {"error": "forbidden", "message": str(exc)})
                except (ValueError, KeyError, json.JSONDecodeError) as exc:
                    self._send_json(400, {"error": "bad_request", "message": str(exc)})
                except Exception as exc:
                    self._send_json(500, {"error": "internal_error", "type": type(exc).__name__})

        return Handler

    def serve_forever(self) -> None:
        self.httpd.serve_forever(poll_interval=0.1)

    def start(self) -> threading.Thread:
        if self._thread is not None and self._thread.is_alive():
            return self._thread
        self._thread = threading.Thread(target=self.serve_forever, name="owner-friend-service", daemon=True)
        self._thread.start()
        return self._thread

    def close(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        if self._thread is not None:
            self._thread.join(timeout=5)
