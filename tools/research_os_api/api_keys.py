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

from api_key_store import APIKeyStore, InMemoryAPIKeyStore, StoredAPIKey


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

    @classmethod
    def from_stored(cls, stored: StoredAPIKey) -> "APIKeyRecord":
        return cls(
            stored.key_id,
            stored.principal_id,
            stored.fingerprint,
            stored.scopes,
            stored.created_at,
            stored.expires_at,
            stored.revoked_at,
        )


class APIKeyManager:
    """API-key lifecycle manager backed by the canonical storage contract."""

    PREFIX = "ro_live_"

    def __init__(self, store: APIKeyStore | None = None) -> None:
        self._store = store or InMemoryAPIKeyStore()

    def create(
        self,
        principal_id: str,
        scopes: set[str] | frozenset[str],
        *,
        expires_at: datetime | None = None,
    ) -> tuple[APIKeyRecord, str]:
        principal_id = principal_id.strip()
        if not principal_id:
            raise APIKeyError("principal_id is required")
        if expires_at is not None and expires_at <= datetime.now(timezone.utc):
            raise APIKeyError("expires_at must be in the future")
        raw = self.PREFIX + secrets.token_urlsafe(32)
        key_id = "key_" + secrets.token_hex(12)
        created = datetime.now(timezone.utc)
        fingerprint = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
        stored = StoredAPIKey(
            key_id,
            principal_id,
            fingerprint,
            _digest(raw),
            frozenset(scopes),
            created,
            expires_at,
        )
        self._store.put(stored)
        return APIKeyRecord.from_stored(stored), raw

    def verify(
        self,
        raw_key: str,
        *,
        required_scope: str | None = None,
        now: datetime | None = None,
    ) -> APIKeyRecord | None:
        if not raw_key.startswith(self.PREFIX):
            return None
        digest = _digest(raw_key)
        current = now or datetime.now(timezone.utc)
        stored = self._store.find_by_digest(digest)
        if stored is None or not hmac.compare_digest(digest, stored.digest):
            return None
        if stored.revoked_at is not None or (stored.expires_at is not None and stored.expires_at <= current):
            return None
        if required_scope and required_scope not in stored.scopes:
            return None
        return APIKeyRecord.from_stored(stored)

    def revoke(self, key_id: str, *, now: datetime | None = None) -> APIKeyRecord:
        revoked = now or datetime.now(timezone.utc)
        try:
            return APIKeyRecord.from_stored(self._store.revoke(key_id, revoked))
        except KeyError as exc:
            raise APIKeyError("unknown key") from exc

    def list(self, principal_id: str | None = None) -> tuple[APIKeyRecord, ...]:
        return tuple(APIKeyRecord.from_stored(item) for item in self._store.list(principal_id))
