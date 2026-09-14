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


class APIKeyError(ValueError):
    pass


def _pepper() -> bytes:
    value = os.getenv("RESEARCH_OS_API_KEY_PEPPER", "").encode("utf-8")
    if not value:
        raise APIKeyError("RESEARCH_OS_API_KEY_PEPPER is required")
    return value


def _digest(raw_key: str) -> str:
    if not raw_key:
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

    def __init__(self) -> None:
        self._records: dict[str, APIKeyRecord] = {}
        self._digests: dict[str, str] = {}

    def create(self, principal_id: str, scopes: set[str] | frozenset[str], *, expires_at: datetime | None = None) -> tuple[APIKeyRecord, str]:
        principal_id = principal_id.strip()
        if not principal_id:
            raise APIKeyError("principal_id is required")
        if expires_at is not None and expires_at <= datetime.now(timezone.utc):
            raise APIKeyError("expires_at must be in the future")
        raw = self.PREFIX + secrets.token_urlsafe(32)
        key_id = "key_" + secrets.token_hex(12)
        created = datetime.now(timezone.utc)
        fingerprint = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
        record = APIKeyRecord(key_id, principal_id, fingerprint, frozenset(scopes), created, expires_at)
        self._records[key_id] = record
        self._digests[key_id] = _digest(raw)
        return record, raw

    def verify(self, raw_key: str, *, required_scope: str | None = None, now: datetime | None = None) -> APIKeyRecord | None:
        if not raw_key.startswith(self.PREFIX):
            return None
        digest = _digest(raw_key)
        current = now or datetime.now(timezone.utc)
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
        revoked = now or datetime.now(timezone.utc)
        updated = APIKeyRecord(record.key_id, record.principal_id, record.fingerprint, record.scopes, record.created_at, record.expires_at, revoked)
        self._records[key_id] = updated
        return updated

    def list(self, principal_id: str | None = None) -> tuple[APIKeyRecord, ...]:
        values = tuple(self._records.values())
        if principal_id is None:
            return values
        return tuple(record for record in values if record.principal_id == principal_id)
