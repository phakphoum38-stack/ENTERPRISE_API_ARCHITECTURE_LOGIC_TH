"""Owner-only switchable Friend transport connector.

FriendRuntime is the canonical execution layer. HTTP 8790 is an optional
transport boundary. This module deliberately contains no workflow, merge,
Render, or authority logic.
"""
from __future__ import annotations

import base64
import json
import os
import threading
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from owner_special.research_os_friend.provider_settings import WindowsDpapiSecretStore
from owner_special.research_os_friend.resource_control_runtime import install_friend_resource_control
from owner_special.research_os_friend.runtime import FriendRuntime
from owner_special.research_os_friend.models import FriendRequest


class FriendConnectionError(RuntimeError):
    pass


@dataclass(frozen=True)
class FriendConnectionProfile:
    id: str
    name: str
    username: str
    transport: str = "auto"
    endpoint: str = "http://127.0.0.1:8790"
    enabled: bool = True
    locked: bool = False
    owner_scope: str = "owner-only"

    def __post_init__(self) -> None:
        for field in ("id", "name", "username"):
            value = getattr(self, field).strip()
            if not value:
                raise ValueError(f"{field} is required")
        if self.transport not in {"auto", "direct", "http"}:
            raise ValueError("transport must be auto, direct, or http")
        if self.owner_scope != "owner-only":
            raise ValueError("connection profiles are owner-only")
        if len(self.id) > 64 or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for ch in self.id):
            raise ValueError("invalid connection id")

    def public_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["password_configured"] = None
        return payload


class ConnectionProfileStore:
    def __init__(self, root: Path, owner_id: str) -> None:
        self.path = Path(root).resolve() / "owners" / owner_id / "connections" / "profiles.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def list(self) -> tuple[FriendConnectionProfile, ...]:
        with self._lock:
            if not self.path.is_file():
                return ()
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(raw, list):
                raise FriendConnectionError("connection profile store is invalid")
            return tuple(FriendConnectionProfile(**dict(item)) for item in raw)

    def get(self, profile_id: str) -> FriendConnectionProfile:
        for profile in self.list():
            if profile.id == profile_id:
                return profile
        raise FriendConnectionError(f"connection profile not found: {profile_id}")

    def upsert(self, profile: FriendConnectionProfile) -> FriendConnectionProfile:
        with self._lock:
            profiles = list(self.list())
            profiles = [item for item in profiles if item.id != profile.id]
            profiles.append(profile)
            temporary = self.path.with_suffix(".json.tmp")
            temporary.write_text(
                json.dumps([asdict(item) for item in sorted(profiles, key=lambda x: x.id)], indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            os.replace(temporary, self.path)
        return profile


class ConnectionCredentialStore:
    """Stores only the password, never in a connection profile.

    Production desktop storage uses the existing Windows DPAPI implementation.
    Non-Windows API servers must not silently downgrade to plaintext storage.
    """

    def __init__(self, root: Path, owner_id: str) -> None:
        if os.name != "nt":
            raise RuntimeError("connection password storage requires the owner desktop secure store")
        path = Path(root).resolve() / "owners" / owner_id / "connections" / "credentials.dpapi"
        self._store = WindowsDpapiSecretStore(path)

    def set(self, profile_id: str, password: str) -> None:
        current = self._read_map()
        current[profile_id] = password
        self._store.write(json.dumps(current, sort_keys=True))

    def get(self, profile_id: str) -> str | None:
        return self._read_map().get(profile_id)

    def _read_map(self) -> dict[str, str]:
        raw = self._store.read()
        if not raw:
            return {}
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise FriendConnectionError("connection credential store is invalid")
        return {str(k): str(v) for k, v in value.items()}


@dataclass
class _Circuit:
    failures: int = 0
    opened_until: float = 0.0

    def open(self) -> bool:
        return time.monotonic() < self.opened_until


class FriendConnector:
    """Switchable Owner-only Friend connector."""

    def __init__(self, *, owner_id: str, data_root: Path, repository_root: Path | None = None) -> None:
        self.owner_id = owner_id
        self.data_root = Path(data_root).resolve()
        self.repository_root = Path(repository_root).resolve() if repository_root else None
        self.profiles = ConnectionProfileStore(self.data_root, owner_id)
        self.credentials = ConnectionCredentialStore(self.data_root, owner_id)
        self._runtime: FriendRuntime | None = None
        self._circuits: dict[str, _Circuit] = {}
        self._lock = threading.RLock()

    def _runtime_or_create(self) -> FriendRuntime:
        with self._lock:
            if self._runtime is None:
                install_friend_resource_control()
                self._runtime = FriendRuntime.create_owner_special(
                    self.owner_id,
                    data_root=self.data_root,
                    repository_root=self.repository_root,
                )
            return self._runtime

    def _http_request(self, profile: FriendConnectionProfile, payload: dict[str, object], session_id: str, password_override: str | None = None) -> dict[str, object]:
        password = password_override if password_override is not None else self.credentials.get(profile.id)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json; charset=utf-8",
            "X-Research-OS-Owner": self.owner_id,
            "X-Research-OS-Profile": profile.id,
            "X-Research-OS-Session": session_id,
        }
        if password is not None:
            token = base64.b64encode(f"{profile.username}:{password}".encode("utf-8")).decode("ascii")
            headers["Authorization"] = f"Basic {token}"
        request = urllib.request.Request(
            profile.endpoint.rstrip("/") + "/owner/chat",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=8) as response:
                value = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise FriendConnectionError(f"HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise FriendConnectionError(f"HTTP unavailable: {exc.reason}") from exc
        if not isinstance(value, dict):
            raise FriendConnectionError("HTTP Friend response is not an object")
        return value

    def _direct_chat(self, payload: dict[str, object], session_id: str) -> dict[str, object]:
        response = self._runtime_or_create().ask(
            FriendRequest(
                owner_id=self.owner_id,
                profile_id="direct",
                session_id=session_id,
                text=str(payload["text"]),
                complexity=int(payload.get("complexity", 3)),
                risk=int(payload.get("risk", 1)),
                parallelism=int(payload.get("parallelism", 2)),
                helper_budget=int(payload.get("helper_budget", 0)),
                requested_skills=tuple(str(item) for item in payload.get("requested_skills", []) or []),
                requested_tools=tuple(str(item) for item in payload.get("requested_tools", []) or []),
            )
        )
        return {
            "provider": response.provider,
            "text": response.text,
            "decision": asdict(response.decision),
            "factory": response.factory,
            "helpers": response.helpers,
            "metadata": response.metadata,
        }

    def _attempt(self, profile: FriendConnectionProfile, transport: str, payload: dict[str, object], session_id: str, password_override: str | None = None) -> dict[str, object]:
        circuit = self._circuits.setdefault(f"{profile.id}:{transport}", _Circuit())
        if circuit.open():
            raise FriendConnectionError("circuit_open")
        try:
            if transport == "direct":
                value = self._direct_chat(payload, session_id)
            else:
                value = self._http_request(profile, payload, session_id, password_override=password_override)
            circuit.failures = 0
            circuit.opened_until = 0.0
            return value
        except Exception:
            circuit.failures += 1
            if circuit.failures >= 3:
                circuit.opened_until = time.monotonic() + 10.0
            raise

    def chat(self, profile_id: str, payload: dict[str, object], *, session_id: str = "main-api", password: str | None = None) -> dict[str, object]:
        profile = self.profiles.get(profile_id)
        if not profile.enabled:
            raise FriendConnectionError("connection profile is disabled")
        transports = [profile.transport] if profile.transport != "auto" else ["direct", "http"]
        errors: list[dict[str, str]] = []
        for transport in transports:
            try:
                result = self._attempt(profile, transport, payload, session_id, password_override=password)
                return {
                    **result,
                    "connection_id": profile.id,
                    "connection_name": profile.name,
                    "transport": transport,
                    "owner_verified": True,
                    "fallback_used": transport != transports[0],
                }
            except Exception as exc:
                errors.append({"transport": transport, "error": str(exc)})
                if profile.locked:
                    break
        raise FriendConnectionError(json.dumps({
            "connection_id": profile.id,
            "transport": profile.transport,
            "owner_verified": True,
            "status": "offline",
            "attempts": errors,
        }, sort_keys=True))

    def test(self, profile_id: str, *, password: str | None = None) -> dict[str, object]:
        profile = self.profiles.get(profile_id)
        result: dict[str, object] = {
            "connection_id": profile.id,
            "connection_name": profile.name,
            "owner_verified": True,
            "transport": profile.transport,
            "enabled": profile.enabled,
            "locked": profile.locked,
            "credential_configured": self.credentials.get(profile.id) is not None,
        }
        if profile.transport in {"auto", "direct"}:
            try:
                runtime = self._runtime_or_create()
                runtime.architecture()
                result["direct_runtime"] = "ready"
            except Exception as exc:
                result["direct_runtime"] = f"error:{type(exc).__name__}"
        if profile.transport in {"auto", "http"}:
            try:
                request = urllib.request.Request(
                    profile.endpoint.rstrip("/") + "/owner/health",
                    headers={"Accept": "application/json"},
                    method="GET",
                )
                with urllib.request.urlopen(request, timeout=3) as response:
                    result["http_bridge"] = json.loads(response.read().decode("utf-8"))
            except Exception as exc:
                result["http_bridge"] = f"error:{type(exc).__name__}"
        result["status"] = "ready" if result.get("direct_runtime") == "ready" or isinstance(result.get("http_bridge"), dict) else "offline"
        return result
