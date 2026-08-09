#!/usr/bin/env python3
"""Owner-approved access control for the separate Research OS Developer Platform.

This module stores only access metadata. It never moves, copies, renames, or
changes ownership of the underlying resource. The owner keeps normal access at
all times; developer access is an overlay that can be approved, narrowed,
expired, or revoked independently.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

_SCHEMA_VERSION = 1
_ALLOWED_SCOPES = {"read", "comment", "write"}
_REQUEST_STATES = {"pending", "approved", "rejected", "cancelled"}


@dataclass
class DeveloperAccessRequest:
    request_id: str
    developer_id: str
    owner_id: str
    workspace_id: str
    resource_id: str
    resource_name: str
    requested_scopes: list[str]
    purpose: str
    status: str = "pending"
    created_at: float = field(default_factory=time.time)
    decided_at: float | None = None
    decision_reason: str | None = None


@dataclass
class DeveloperAccessGrant:
    grant_id: str
    request_id: str
    developer_id: str
    owner_id: str
    workspace_id: str
    resource_id: str
    resource_name: str
    scopes: list[str]
    created_at: float = field(default_factory=time.time)
    expires_at: float | None = None
    revoked_at: float | None = None
    revoke_reason: str | None = None

    @property
    def active(self) -> bool:
        now = time.time()
        return self.revoked_at is None and (self.expires_at is None or self.expires_at > now)


class DeveloperAccessStore:
    """Durable approval/grant store for Developer Platform access."""

    def __init__(self, data_dir: str | Path) -> None:
        self.root = Path(data_dir) / "developer-access"
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "access-control.json"
        self._lock = threading.RLock()
        self._requests: dict[str, DeveloperAccessRequest] = {}
        self._grants: dict[str, DeveloperAccessGrant] = {}
        self._load()

    @staticmethod
    def _normalize_scopes(scopes: Iterable[str]) -> list[str]:
        normalized = sorted({str(scope).strip().lower() for scope in scopes if str(scope).strip()})
        if not normalized:
            raise ValueError("at least one access scope is required")
        invalid = set(normalized) - _ALLOWED_SCOPES
        if invalid:
            raise ValueError(f"unsupported access scopes: {', '.join(sorted(invalid))}")
        return normalized

    def request_access(
        self,
        *,
        developer_id: str,
        owner_id: str,
        workspace_id: str,
        resource_id: str,
        resource_name: str,
        requested_scopes: Iterable[str],
        purpose: str,
    ) -> dict[str, Any]:
        developer_id = developer_id.strip()
        owner_id = owner_id.strip()
        workspace_id = workspace_id.strip()
        resource_id = resource_id.strip()
        resource_name = resource_name.strip() or resource_id
        purpose = purpose.strip()
        if not developer_id or not owner_id or not workspace_id or not resource_id:
            raise ValueError("developer_id, owner_id, workspace_id and resource_id are required")
        if developer_id == owner_id:
            raise ValueError("resource owner does not need a developer access grant")
        if not purpose:
            raise ValueError("access purpose is required")
        scopes = self._normalize_scopes(requested_scopes)
        with self._lock:
            for item in self._requests.values():
                if (
                    item.status == "pending"
                    and item.developer_id == developer_id
                    and item.owner_id == owner_id
                    and item.workspace_id == workspace_id
                    and item.resource_id == resource_id
                ):
                    raise ValueError("an access request is already pending for this resource")
            item = DeveloperAccessRequest(
                request_id=str(uuid.uuid4()),
                developer_id=developer_id,
                owner_id=owner_id,
                workspace_id=workspace_id,
                resource_id=resource_id,
                resource_name=resource_name,
                requested_scopes=scopes,
                purpose=purpose,
            )
            self._requests[item.request_id] = item
            self._persist()
            return self._request_payload(item)

    def approve_request(
        self,
        *,
        owner_id: str,
        request_id: str,
        scopes: Iterable[str] | None = None,
        expires_in_seconds: int | None = None,
    ) -> dict[str, Any]:
        owner_id = owner_id.strip()
        with self._lock:
            request = self._require_request(request_id)
            if request.owner_id != owner_id:
                raise PermissionError("only the resource owner can approve this request")
            if request.status != "pending":
                raise ValueError(f"request is already {request.status}")
            granted_scopes = self._normalize_scopes(scopes or request.requested_scopes)
            if not set(granted_scopes).issubset(set(request.requested_scopes)):
                raise ValueError("owner may narrow requested scopes but cannot add unrequested scopes")
            expires_at = None
            if expires_in_seconds is not None:
                if expires_in_seconds < 60:
                    raise ValueError("grant expiry must be at least 60 seconds")
                expires_at = time.time() + int(expires_in_seconds)
            request.status = "approved"
            request.decided_at = time.time()
            grant = DeveloperAccessGrant(
                grant_id=str(uuid.uuid4()),
                request_id=request.request_id,
                developer_id=request.developer_id,
                owner_id=request.owner_id,
                workspace_id=request.workspace_id,
                resource_id=request.resource_id,
                resource_name=request.resource_name,
                scopes=granted_scopes,
                expires_at=expires_at,
            )
            self._grants[grant.grant_id] = grant
            self._persist()
            return self._grant_payload(grant)

    def reject_request(self, *, owner_id: str, request_id: str, reason: str = "") -> dict[str, Any]:
        owner_id = owner_id.strip()
        with self._lock:
            request = self._require_request(request_id)
            if request.owner_id != owner_id:
                raise PermissionError("only the resource owner can reject this request")
            if request.status != "pending":
                raise ValueError(f"request is already {request.status}")
            request.status = "rejected"
            request.decided_at = time.time()
            request.decision_reason = reason.strip() or None
            self._persist()
            return self._request_payload(request)

    def cancel_request(self, *, developer_id: str, request_id: str) -> dict[str, Any]:
        developer_id = developer_id.strip()
        with self._lock:
            request = self._require_request(request_id)
            if request.developer_id != developer_id:
                raise PermissionError("only the requesting developer can cancel this request")
            if request.status != "pending":
                raise ValueError(f"request is already {request.status}")
            request.status = "cancelled"
            request.decided_at = time.time()
            self._persist()
            return self._request_payload(request)

    def revoke_grant(self, *, owner_id: str, grant_id: str, reason: str = "") -> dict[str, Any]:
        owner_id = owner_id.strip()
        with self._lock:
            grant = self._require_grant(grant_id)
            if grant.owner_id != owner_id:
                raise PermissionError("only the resource owner can revoke this grant")
            if grant.revoked_at is None:
                grant.revoked_at = time.time()
                grant.revoke_reason = reason.strip() or None
                self._persist()
            return self._grant_payload(grant)

    def authorize(
        self,
        *,
        principal_id: str,
        owner_id: str,
        workspace_id: str,
        resource_id: str,
        scope: str,
    ) -> dict[str, Any]:
        """Evaluate access without changing ownership of the underlying resource."""
        principal_id = principal_id.strip()
        owner_id = owner_id.strip()
        scope = scope.strip().lower()
        if scope not in _ALLOWED_SCOPES:
            raise ValueError(f"unsupported access scope: {scope}")
        if principal_id == owner_id:
            return {
                "allowed": True,
                "mode": "owner",
                "owner_access_unchanged": True,
                "grant_id": None,
            }
        with self._lock:
            for grant in self._grants.values():
                if (
                    grant.active
                    and grant.developer_id == principal_id
                    and grant.owner_id == owner_id
                    and grant.workspace_id == workspace_id
                    and grant.resource_id == resource_id
                    and scope in grant.scopes
                ):
                    return {
                        "allowed": True,
                        "mode": "developer_grant",
                        "owner_access_unchanged": True,
                        "grant_id": grant.grant_id,
                        "expires_at": grant.expires_at,
                    }
        return {
            "allowed": False,
            "mode": "no_active_grant",
            "owner_access_unchanged": True,
            "grant_id": None,
        }

    def list_owner_requests(self, owner_id: str, *, status: str | None = None) -> list[dict[str, Any]]:
        if status is not None and status not in _REQUEST_STATES:
            raise ValueError("invalid request status")
        with self._lock:
            items = [
                item for item in self._requests.values()
                if item.owner_id == owner_id and (status is None or item.status == status)
            ]
            items.sort(key=lambda item: item.created_at, reverse=True)
            return [self._request_payload(item) for item in items]

    def list_developer_requests(self, developer_id: str) -> list[dict[str, Any]]:
        with self._lock:
            items = [item for item in self._requests.values() if item.developer_id == developer_id]
            items.sort(key=lambda item: item.created_at, reverse=True)
            return [self._request_payload(item) for item in items]

    def list_developer_grants(self, developer_id: str, *, active_only: bool = True) -> list[dict[str, Any]]:
        with self._lock:
            items = [item for item in self._grants.values() if item.developer_id == developer_id]
            if active_only:
                items = [item for item in items if item.active]
            items.sort(key=lambda item: item.created_at, reverse=True)
            return [self._grant_payload(item) for item in items]

    def list_owner_grants(self, owner_id: str, *, active_only: bool = True) -> list[dict[str, Any]]:
        with self._lock:
            items = [item for item in self._grants.values() if item.owner_id == owner_id]
            if active_only:
                items = [item for item in items if item.active]
            items.sort(key=lambda item: item.created_at, reverse=True)
            return [self._grant_payload(item) for item in items]

    def _require_request(self, request_id: str) -> DeveloperAccessRequest:
        try:
            return self._requests[request_id]
        except KeyError as exc:
            raise ValueError(f"unknown access request: {request_id}") from exc

    def _require_grant(self, grant_id: str) -> DeveloperAccessGrant:
        try:
            return self._grants[grant_id]
        except KeyError as exc:
            raise ValueError(f"unknown access grant: {grant_id}") from exc

    @staticmethod
    def _request_payload(item: DeveloperAccessRequest) -> dict[str, Any]:
        return asdict(item)

    @staticmethod
    def _grant_payload(item: DeveloperAccessGrant) -> dict[str, Any]:
        payload = asdict(item)
        payload["active"] = item.active
        payload["owner_access_unchanged"] = True
        return payload

    def _load(self) -> None:
        if not self.path.exists():
            return
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != _SCHEMA_VERSION:
            raise RuntimeError("unsupported developer access schema")
        for raw in payload.get("requests", []):
            item = DeveloperAccessRequest(**raw)
            self._requests[item.request_id] = item
        for raw in payload.get("grants", []):
            raw = dict(raw)
            raw.pop("active", None)
            raw.pop("owner_access_unchanged", None)
            item = DeveloperAccessGrant(**raw)
            self._grants[item.grant_id] = item

    def _persist(self) -> None:
        payload = {
            "schema_version": _SCHEMA_VERSION,
            "requests": [asdict(item) for item in self._requests.values()],
            "grants": [asdict(item) for item in self._grants.values()],
        }
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temp.replace(self.path)
