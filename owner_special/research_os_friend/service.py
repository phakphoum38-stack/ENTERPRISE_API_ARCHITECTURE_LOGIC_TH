from __future__ import annotations

import json
import os
import re
import threading
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .launch_desk_agent import stream_launch_desk
from .models import FriendRequest
from .provider_settings import ProviderManager
from .resource_control_runtime import install_friend_resource_control
from .runtime import FriendRuntime
from .schedule_generation.preview import PreviewNotFoundError

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

    def __init__(self, *, owner_id: str, host: str = "127.0.0.1", port: int = 8790, data_root: Path | None = None, repository_root: Path | None = None, audit_path: Path | None = None, provider_manager: ProviderManager | None = None) -> None:
        if host != "127.0.0.1":
            raise ValueError("Owner Friend Service must bind to 127.0.0.1")
        self.host = host
        self.data_root = Path(data_root or default_owner_data_root()).resolve()
        self.audit_path = Path(audit_path).resolve() if audit_path is not None else None
        self.runtime = FriendRuntime.create_owner_special(owner_id, data_root=self.data_root, repository_root=repository_root)
        install_friend_resource_control()
        self.provider_manager = provider_manager or ProviderManager(self.data_root, owner_id)
        self._apply_provider()
        self.httpd = ThreadingHTTPServer((host, port), self._make_handler())
        self.port = int(self.httpd.server_address[1])
        self._thread: threading.Thread | None = None

    def _apply_provider(self) -> None:
        self.runtime.orchestrator.providers.remove("openai-compatible")
        provider = self.provider_manager.provider()
        if provider is not None:
            self.runtime.orchestrator.providers.set_primary(provider)

    def _make_handler(self):
        service = self

        class Handler(BaseHTTPRequestHandler):
            server_version = "ResearchOSOwnerFriend/1.3"

            def log_message(self, format: str, *args: object) -> None:
                return

            def _audit(self, status: int) -> None:
                if service.audit_path is None:
                    return
                service.audit_path.parent.mkdir(parents=True, exist_ok=True)
                record = {"method": self.command, "path": urlparse(self.path).path, "status": int(status)}
                with service.audit_path.open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(record, sort_keys=True) + "\n")

            def _send_json(self, status: int, payload: dict[str, object]) -> None:
                body = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _headers(self) -> tuple[str, str, str]:
                owner_id = _safe_scope(self.headers.get(OWNER_HEADER, ""), "owner")
                profile_id = _safe_scope(self.headers.get(PROFILE_HEADER, "default"), "profile")
                session_id = _safe_scope(self.headers.get(SESSION_HEADER, "default"), "session")
                return owner_id, profile_id, session_id

            def _request(self, payload: dict[str, object]) -> FriendRequest:
                owner_id, profile_id, session_id = self._headers()
                text = str(payload.get("text", "")).strip()
                if not text:
                    raise ValueError("text is required")
                requested_tools = tuple(str(item) for item in payload.get("requested_tools", ()) or ())
                requested_skills = tuple(str(item) for item in payload.get("requested_skills", ()) or ())
                return FriendRequest(owner_id=owner_id, profile_id=profile_id, session_id=session_id, text=text, requested_tools=requested_tools, requested_skills=requested_skills)

            def do_GET(self) -> None:
                path = urlparse(self.path).path
                try:
                    if path == "/owner/health":
                        self._send_json(200, {"status": "ok", "version": "1.3.1-owner", "loopback_only": True, "server": self.server_version})
                        return
                    if path == "/owner/status":
                        self._headers()
                        self._send_json(200, {"status": "ok", "architecture": service.runtime.architecture()})
                        return
                    self._send_json(404, {"error": "not_found"})
                except PermissionError as exc:
                    self._send_json(403, {"error": str(exc)})
                except ValueError as exc:
                    self._send_json(400, {"error": str(exc)})
                except Exception as exc:
                    self._send_json(500, {"error": type(exc).__name__})

            def do_POST(self) -> None:
                path = urlparse(self.path).path
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    payload = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
                    if not isinstance(payload, dict):
                        raise ValueError("JSON object required")
                    if path == "/owner/chat":
                        response = service.runtime.ask(self._request(payload))
                        self._send_json(200, {"text": response.text, "provider": response.provider, "memory_items": response.memory_items, "evidence_id": response.evidence_id, "metadata": response.metadata, "decision": asdict(response.decision)})
                        return
                    if path == "/owner/launch-desk/stream":
                        request = self._request(payload)
                        for event in stream_launch_desk(service.runtime, request):
                            self._send_json(200, event)
                        return
                    self._send_json(404, {"error": "not_found"})
                except PermissionError as exc:
                    self._send_json(403, {"error": str(exc)})
                except ValueError as exc:
                    self._send_json(400, {"error": str(exc)})
                except Exception as exc:
                    self._send_json(500, {"error": type(exc).__name__})

        return Handler

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self.httpd.serve_forever, name="research-os-owner-friend", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None
