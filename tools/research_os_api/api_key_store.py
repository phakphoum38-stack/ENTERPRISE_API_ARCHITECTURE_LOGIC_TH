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


class JsonAPIKeyStore:
    """Durable API-key adapter; stores digests/fingerprints only, never raw secrets."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        if not self.path.exists():
            self._write({})

    def _read(self) -> dict[str, dict]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            raise RuntimeError("API-key store is unavailable or corrupt") from exc

    def _write(self, data: dict[str, dict]) -> None:
        fd, tmp = tempfile.mkstemp(prefix=self.path.name + ".", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, sort_keys=True, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp, self.path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    @staticmethod
    def _encode(record: StoredAPIKey) -> dict:
        return {
            "key_id": record.key_id,
            "principal_id": record.principal_id,
            "fingerprint": record.fingerprint,
            "digest": record.digest,
            "scopes": sorted(record.scopes),
            "created_at": record.created_at.isoformat(),
            "expires_at": record.expires_at.isoformat() if record.expires_at else None,
            "revoked_at": record.revoked_at.isoformat() if record.revoked_at else None,
        }

    @staticmethod
    def _decode(payload: dict) -> StoredAPIKey:
        return StoredAPIKey(
            payload["key_id"], payload["principal_id"], payload["fingerprint"],
            payload["digest"], frozenset(payload.get("scopes", [])),
            datetime.fromisoformat(payload["created_at"]),
            datetime.fromisoformat(payload["expires_at"]) if payload.get("expires_at") else None,
            datetime.fromisoformat(payload["revoked_at"]) if payload.get("revoked_at") else None,
        )

    def put(self, record: StoredAPIKey) -> None:
        with self._lock:
            data = self._read()
            data[record.key_id] = self._encode(record)
            self._write(data)

    def get(self, key_id: str) -> StoredAPIKey | None:
        with self._lock:
            value = self._read().get(key_id)
            return self._decode(value) if value else None

    def find_by_digest(self, digest: str) -> StoredAPIKey | None:
        with self._lock:
            for value in self._read().values():
                if value.get("digest") == digest:
                    return self._decode(value)
        return None

    def revoke(self, key_id: str, revoked_at: datetime) -> StoredAPIKey:
        with self._lock:
            current = self.get(key_id)
            if current is None:
                raise KeyError(key_id)
            updated = StoredAPIKey(
                current.key_id, current.principal_id, current.fingerprint, current.digest,
                current.scopes, current.created_at, current.expires_at,
                current.revoked_at or revoked_at,
            )
            self.put(updated)
            return updated

    def list(self, principal_id: str | None = None) -> tuple[StoredAPIKey, ...]:
        with self._lock:
            values = tuple(self._decode(value) for value in self._read().values())
        if principal_id is None:
            return values
        return tuple(value for value in values if value.principal_id == principal_id)
