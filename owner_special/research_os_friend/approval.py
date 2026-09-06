from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from threading import RLock
from typing import TYPE_CHECKING

from .identity import OwnerIdentity
from .models import FriendRequest

if TYPE_CHECKING:
    from .approval_store import PersistentApprovalStore


class ApprovalState(str, Enum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"


# Known side-effect surfaces are explicitly approval-gated. Unknown tools are
# not granted implicit approval by this module.
SIDE_EFFECT_TOOLS = frozenset(
    {
        "shell",
        "shell.run",
        "github-actions",
        "github.actions",
        "github-repository",
        "github.repository.manage",
        "git-branch",
        "git.branch",
        "pr-gate",
        "git.pull_request",
    }
)


@dataclass(frozen=True)
class ApprovalRecord:
    approval_id: str
    owner_id: str
    profile_id: str
    session_id: str
    tool_name: str
    request_fingerprint: str
    state: ApprovalState
    created_at: str
    decided_at: str | None = None
    reason: str = ""


class ApprovalGate:
    """Owner-scoped approval state for explicitly side-effecting tools."""

    def __init__(
        self,
        required_tools: frozenset[str] = SIDE_EFFECT_TOOLS,
        store: PersistentApprovalStore | None = None,
    ) -> None:
        self._required_tools = frozenset(required_tools)
        self._store = store
        self._records: dict[str, ApprovalRecord] = {
            record.approval_id: record for record in (store.load() if store is not None else ())
        }
        self._lock = RLock()

    @staticmethod
    def _fingerprint(request: FriendRequest, tool_name: str) -> str:
        payload = {
            "owner_id": request.owner_id,
            "profile_id": request.profile_id,
            "session_id": request.session_id,
            "text": request.text,
            "tool_name": tool_name,
        }
        return hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()

    def _persist(self) -> None:
        if self._store is None:
            return
        self._store.save(self._records.values())

    def requires_approval(self, tool_name: str) -> bool:
        return tool_name in self._required_tools

    def inspect(self, owner: OwnerIdentity, request: FriendRequest, tool_name: str) -> ApprovalRecord:
        if not owner.matches(request.owner_id):
            raise PermissionError("approval request does not match the configured owner")
        if tool_name not in request.requested_tools:
            raise PermissionError(f"tool was not explicitly requested: {tool_name}")
        fingerprint = self._fingerprint(request, tool_name)
        approval_id = hashlib.sha256(fingerprint.encode("ascii")).hexdigest()
        if not self.requires_approval(tool_name):
            return ApprovalRecord(
                approval_id=approval_id,
                owner_id=owner.owner_id,
                profile_id=request.profile_id,
                session_id=request.session_id,
                tool_name=tool_name,
                request_fingerprint=fingerprint,
                state=ApprovalState.NOT_REQUIRED,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
        with self._lock:
            existing = self._records.get(approval_id)
            if existing is not None:
                return existing
            record = ApprovalRecord(
                approval_id=approval_id,
                owner_id=owner.owner_id,
                profile_id=request.profile_id,
                session_id=request.session_id,
                tool_name=tool_name,
                request_fingerprint=fingerprint,
                state=ApprovalState.PENDING,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            self._records[approval_id] = record
            self._persist()
            return record

    def decide(
        self,
        owner: OwnerIdentity,
        request: FriendRequest,
        tool_name: str,
        *,
        state: ApprovalState,
        reason: str = "",
    ) -> ApprovalRecord:
        if state not in (ApprovalState.APPROVED, ApprovalState.DENIED):
            raise ValueError("decision state must be approved or denied")
        current = self.inspect(owner, request, tool_name)
        if current.state is ApprovalState.NOT_REQUIRED:
            return current
        if current.state is not ApprovalState.PENDING:
            if current.state is state:
                return current
            raise PermissionError(f"approval already decided: {current.state.value}")
        updated = replace(
            current,
            state=state,
            decided_at=datetime.now(timezone.utc).isoformat(),
            reason=reason,
        )
        with self._lock:
            self._records[current.approval_id] = updated
            self._persist()
        return updated

    def approve(self, owner: OwnerIdentity, request: FriendRequest, tool_name: str, reason: str = "") -> ApprovalRecord:
        return self.decide(owner, request, tool_name, state=ApprovalState.APPROVED, reason=reason)

    def deny(self, owner: OwnerIdentity, request: FriendRequest, tool_name: str, reason: str = "") -> ApprovalRecord:
        return self.decide(owner, request, tool_name, state=ApprovalState.DENIED, reason=reason)

    def enforce(self, owner: OwnerIdentity, request: FriendRequest, tool_name: str) -> ApprovalRecord:
        record = self.inspect(owner, request, tool_name)
        if record.state is ApprovalState.PENDING:
            raise PermissionError(f"approval required before executing tool: {tool_name}; approval_id={record.approval_id}")
        if record.state is ApprovalState.DENIED:
            raise PermissionError(f"tool execution denied: {tool_name}; approval_id={record.approval_id}")
        return record

    def get(self, approval_id: str) -> ApprovalRecord | None:
        with self._lock:
            return self._records.get(approval_id)

    def list(self, *, owner_id: str | None = None) -> tuple[ApprovalRecord, ...]:
        with self._lock:
            records = tuple(self._records.values())
        if owner_id is not None:
            records = tuple(record for record in records if record.owner_id == owner_id)
        return tuple(sorted(records, key=lambda item: (item.created_at, item.approval_id)))
