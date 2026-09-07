"""Fail-closed governance boundary for the existing Friend runtime in H4."""

from __future__ import annotations

import copy
import json
import re
from collections.abc import Mapping
from typing import Any

from .models import FriendRequest
from .runtime import FriendRuntime


class FriendRuntimeContractError(ValueError):
    """Raised when a governed runtime operation is unsafe or unbound."""


class FriendRuntimeContract:
    """Bind existing FriendRuntime operations to Owner and source identity."""

    SCHEMA = "research-os-friend-runtime/v1"
    MAX_TEXT = 2048
    MAX_BYTES = 64 * 1024
    MAX_RUNS = 64
    SHA_RE = re.compile(r"^[0-9a-f]{40}$")
    CORRELATION_RE = re.compile(r"^[A-Za-z0-9._:-]{1,2048}$")
    BLOCKED_KEYS = re.compile(
        r"(?:approval|approve|authorize|permission|release|merge|dispatch|"
        r"credential|secret|token|password|private.?key|api.?key|callback|callable|"
        r"function|lambda|eval|exec|shell|command|process|subprocess|"
        r"computer.?use|mcp)",
        re.I,
    )
    BLOCKED_VALUES = re.compile(
        r"(?:BEGIN PRIVATE KEY|ghp_|sk-proj-|javascript:|data:text/html|"
        r"powershell|cmd\.exe|bash\s+-c|os\.system|child_process)",
        re.I,
    )

    def __init__(self, runtime: FriendRuntime, *, owner_id: str, expected_source_sha: str) -> None:
        self._validate_text(owner_id, "owner_id")
        self._validate_sha(expected_source_sha, "expected_source_sha")
        if not isinstance(runtime, FriendRuntime):
            raise FriendRuntimeContractError("runtime must be FriendRuntime")
        if runtime.owner.owner_id != owner_id:
            raise FriendRuntimeContractError("runtime owner mismatch")
        source_sha = str(runtime.source_commit).strip()
        if not self.SHA_RE.fullmatch(source_sha):
            raise FriendRuntimeContractError("runtime source commit is missing or malformed")
        if source_sha != expected_source_sha:
            raise FriendRuntimeContractError("runtime source SHA mismatch")
        self._runtime = runtime
        self.owner_id = owner_id
        self.source_sha = expected_source_sha

    def snapshot(self) -> dict[str, Any]:
        runs = self._runtime.agent_runs()
        if len(runs) > self.MAX_RUNS:
            raise FriendRuntimeContractError("runtime run list exceeds bound")
        run_items = []
        for run in runs:
            item = {"run_id": getattr(run, "run_id", ""), "owner_id": getattr(run, "owner_id", ""), "state": getattr(run, "state", "")}
            self._walk_safe(item)
            run_items.append(item)
        payload = {"schema": self.SCHEMA, "owner_id": self.owner_id, "source_sha": self.source_sha, "read_only": True, "tool_health": copy.deepcopy(self._runtime.tool_health_gate()), "agent_runs": run_items}
        self._validate_payload(payload)
        return copy.deepcopy(payload)

    def ask(self, request: FriendRequest) -> Any:
        self._validate_request(request)
        return self._runtime.ask(request)

    def run_agent(self, request: FriendRequest, *, run_correlation_id: str) -> dict[str, Any]:
        self._validate_request(request)
        self._validate_correlation(run_correlation_id)
        run = self._runtime.run_agent(request)
        envelope = {"schema": self.SCHEMA, "owner_id": self.owner_id, "source_sha": self.source_sha, "run_correlation_id": run_correlation_id, "run_id": getattr(run, "run_id", ""), "state": getattr(run, "state", ""), "read_only": True}
        self._validate_payload(envelope)
        return copy.deepcopy(envelope)

    def get_agent_run(self, run_id: str) -> Any:
        self._validate_text(run_id, "run_id")
        result = self._runtime.get_agent_run(run_id)
        if result is not None:
            self._walk_safe({"run_id": getattr(result, "run_id", ""), "owner_id": getattr(result, "owner_id", ""), "state": getattr(result, "state", "")})
        return result

    def tool_health(self) -> dict[str, Any]:
        result = copy.deepcopy(self._runtime.tool_health_gate())
        self._validate_payload(result)
        return copy.deepcopy(result)

    def _validate_request(self, request: FriendRequest) -> None:
        if not isinstance(request, FriendRequest):
            raise FriendRuntimeContractError("request must be FriendRequest")
        if getattr(request, "owner_id", self.owner_id) != self.owner_id:
            raise FriendRuntimeContractError("request owner mismatch")

    def _validate_payload(self, value: Mapping[str, Any]) -> None:
        if not isinstance(value, Mapping):
            raise FriendRuntimeContractError("runtime payload must be an object")
        self._walk_safe(value)
        if len(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")) > self.MAX_BYTES:
            raise FriendRuntimeContractError("runtime payload exceeds byte bound")

    def _walk_safe(self, value: Any, *, depth: int = 0) -> None:
        if depth > 6:
            raise FriendRuntimeContractError("runtime payload nesting exceeds bound")
        if isinstance(value, Mapping):
            if len(value) > self.MAX_RUNS:
                raise FriendRuntimeContractError("runtime mapping exceeds bound")
            for key, child in value.items():
                if not isinstance(key, str) or len(key) > self.MAX_TEXT or self.BLOCKED_KEYS.search(key):
                    raise FriendRuntimeContractError("runtime payload contains forbidden field")
                self._walk_safe(child, depth=depth + 1)
            return
        if isinstance(value, (list, tuple)):
            if len(value) > self.MAX_RUNS:
                raise FriendRuntimeContractError("runtime collection exceeds bound")
            for child in value:
                self._walk_safe(child, depth=depth + 1)
            return
        if isinstance(value, str):
            if len(value) > self.MAX_TEXT or self.BLOCKED_VALUES.search(value):
                raise FriendRuntimeContractError("runtime payload contains forbidden value")
            return
        if value is None or isinstance(value, (bool, int, float)):
            return
        raise FriendRuntimeContractError("runtime payload contains dynamic value")

    def _validate_text(self, value: str, name: str) -> None:
        if not isinstance(value, str) or not value or len(value) > self.MAX_TEXT:
            raise FriendRuntimeContractError(f"{name} is invalid or oversized")

    def _validate_sha(self, value: str, name: str) -> None:
        if not isinstance(value, str) or not self.SHA_RE.fullmatch(value):
            raise FriendRuntimeContractError(f"{name} must be an exact lowercase commit SHA")

    def _validate_correlation(self, value: str) -> None:
        if not isinstance(value, str) or not self.CORRELATION_RE.fullmatch(value):
            raise FriendRuntimeContractError("run correlation ID is invalid or oversized")
