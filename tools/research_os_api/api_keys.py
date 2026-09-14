"""Research OS API-key primitives.

Keys are credentials for Research OS identities. Provider credentials are a
separate concern and must never be stored in this record.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entitlements import EntitlementRegistry


class APIKeyError(ValueError):
    pass


def _pepper() -> bytes:
    value = os.getenv("RESEARCH_OS_API_KEY_PEPPER", "").encode("utf-8")
    if not value:
        raise APIKeyError("RESEARCH_OS_API_KEY_PEPPER is required")
    return value


def _digest(raw_key: str) -> str:
    if not isinstance(raw_key, str) or not raw_key:
        raise APIKeyError("API key is required")
    return hashlib.sha256(_pepper() + raw_key.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class APIKeyRecord:
    key_id: str
    principal_id: str
    fingerprint: str
    scopes: frozenset[str]
    created_at: datetime
    expires_at: datetime | None
    revoked_at: datetime | None = None

    @property
    def active(self) -> bool:
        now = datetime.now(timezone.utc)
        return self.revoked_at is None and (self.expires_at is None or self.expires_at > now)


class APIKeyManager:
    """In-memory lifecycle manager; persistence belongs to the canonical storage adapter."""

    PREFIX = "ro_live_"

    def __init__(self, *, entitlements: EntitlementRegistry | None = None) -> None:
        self._records: dict[str, APIKeyRecord] = {}
        self._digests: dict[str, str] = {}
        self._entitlements = entitlements

    def create(self, principal_id: str, scopes: set[str] | frozenset[str], *, expires_at: datetime | None = None) -> tuple[APIKeyRecord, str]:
        principal_id = principal_id.strip()
        if not principal_id:
            raise APIKeyError("principal_id is required")
        normalized_scopes = frozenset(scopes)
        if any(not isinstance(scope, str) or not scope.strip() for scope in normalized_scopes):
            raise APIKeyError("scopes must be non-empty strings")
        if expires_at is not None:
            if expires_at.tzinfo is None:
                raise APIKeyError("expires_at must be timezone-aware")
            if expires_at <= datetime.now(timezone.utc):
                raise APIKeyError("expires_at must be in the future")
        if self._entitlements is not None:
            try:
                binding = self._entitlements.get(principal_id)
            except Exception as exc:
                raise APIKeyError("principal entitlement is unavailable") from exc
            if not normalized_scopes.issubset(binding.entitlement.scopes):
                raise APIKeyError("key scopes exceed principal entitlement")
        raw = self.PREFIX + secrets.token_urlsafe(32)
        key_id = "key_" + secrets.token_hex(12)
        created = datetime.now(timezone.utc)
        fingerprint = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
        record = APIKeyRecord(key_id, principal_id, fingerprint, normalized_scopes, created, expires_at)
        self._records[key_id] = record
        self._digests[key_id] = _digest(raw)
        return record, raw

    def verify(self, raw_key: str, *, required_scope: str | None = None, now: datetime | None = None) -> APIKeyRecord | None:
        if not isinstance(raw_key, str) or not raw_key.startswith(self.PREFIX):
            return None
        if required_scope is not None:
            required_scope = required_scope.strip()
            if not required_scope:
                return None
        digest = _digest(raw_key)
        current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        for key_id, stored in self._digests.items():
            if hmac.compare_digest(digest, stored):
                record = self._records[key_id]
                if record.revoked_at is not None or (record.expires_at is not None and record.expires_at <= current):
                    return None
                if required_scope and required_scope not in record.scopes:
                    return None
                return record
        return None

    def revoke(self, key_id: str, *, now: datetime | None = None) -> APIKeyRecord:
        try:
            record = self._records[key_id]
        except KeyError as exc:
            raise APIKeyError("unknown key") from exc
        if record.revoked_at is not None:
            return record
        revoked = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        updated = APIKeyRecord(record.key_id, record.principal_id, record.fingerprint, record.scopes, record.created_at, record.expires_at, revoked)
        self._records[key_id] = updated
        return updated

    def rotate(self, key_id: str, *, expires_at: datetime | None = None, now: datetime | None = None) -> tuple[APIKeyRecord, str]:
        try:
            record = self._records[key_id]
        except KeyError as exc:
            raise APIKeyError("unknown key") from exc
        current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        if record.revoked_at is not None or (record.expires_at is not None and record.expires_at <= current):
            raise APIKeyError("cannot rotate inactive key")
        if expires_at is not None and expires_at.astimezone(timezone.utc) <= current:
            raise APIKeyError("expires_at must be in the future")
        self.revoke(key_id, now=current)
        return self.create(record.principal_id, record.scopes, expires_at=expires_at)

    def list(self, principal_id: str | None = None) -> tuple[APIKeyRecord, ...]:
        values = tuple(self._records.values())
        if principal_id is None:
            return values
        return tuple(record for record in values if record.principal_id == principal_id)
