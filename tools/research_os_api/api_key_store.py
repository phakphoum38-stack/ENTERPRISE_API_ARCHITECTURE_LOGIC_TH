"""Canonical persistence boundary for Research OS API-key records.

The API-key lifecycle manager owns credential generation and verification
semantics. This module owns the persistence contract so runtime integrations
do not depend on an in-memory dictionary implementation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class StoredAPIKey:
    key_id: str
    principal_id: str
    fingerprint: str
    digest: str
    scopes: frozenset[str]
    created_at: datetime
    expires_at: datetime | None
    revoked_at: datetime | None = None


class APIKeyStore(Protocol):
    """Minimal canonical persistence contract for API-key records."""

    def put(self, record: StoredAPIKey) -> None: ...
    def get(self, key_id: str) -> StoredAPIKey | None: ...
    def find_by_digest(self, digest: str) -> StoredAPIKey | None: ...
    def revoke(self, key_id: str, revoked_at: datetime) -> StoredAPIKey: ...
    def list(self, principal_id: str | None = None) -> tuple[StoredAPIKey, ...]: ...


class InMemoryAPIKeyStore:
    """Deterministic test/development adapter for the canonical store contract."""

    def __init__(self) -> None:
        self._records: dict[str, StoredAPIKey] = {}

    def put(self, record: StoredAPIKey) -> None:
        self._records[record.key_id] = record

    def get(self, key_id: str) -> StoredAPIKey | None:
        return self._records.get(key_id)

    def find_by_digest(self, digest: str) -> StoredAPIKey | None:
        for record in self._records.values():
            if record.digest == digest:
                return record
        return None

    def revoke(self, key_id: str, revoked_at: datetime) -> StoredAPIKey:
        record = self._records.get(key_id)
        if record is None:
            raise KeyError(key_id)
        if record.revoked_at is not None:
            return record
        updated = StoredAPIKey(
            record.key_id,
            record.principal_id,
            record.fingerprint,
            record.digest,
            record.scopes,
            record.created_at,
            record.expires_at,
            revoked_at,
        )
        self._records[key_id] = updated
        return updated

    def list(self, principal_id: str | None = None) -> tuple[StoredAPIKey, ...]:
        values = tuple(self._records.values())
        if principal_id is None:
            return values
        return tuple(record for record in values if record.principal_id == principal_id)
