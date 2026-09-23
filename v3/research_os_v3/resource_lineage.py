from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


def _sha256(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class ResourceVersion:
    resource_id: str
    version: int
    content_sha256: str
    parent_version: int | None
    created_at: str


@dataclass(frozen=True)
class ConflictEvidence:
    conflict_id: str
    resource_id: str
    expected_version: int
    expected_sha256: str
    actual_version: int
    actual_sha256: str
    action: str
    execution_disposition: str = "stop"
    resource_disposition: str = "release"
    delivery_disposition: str = "ack_or_reconcile"


class ResourceConflictError(RuntimeError):
    def __init__(self, evidence: ConflictEvidence) -> None:
        self.evidence = evidence
        super().__init__(
            f"stale resource mutation rejected: {evidence.resource_id} "
            f"expected={evidence.expected_version}/{evidence.expected_sha256} "
            f"actual={evidence.actual_version}/{evidence.actual_sha256}"
        )


class ResourceVersionStore:
    """Durable optimistic-concurrency boundary for versioned resources."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS resource_versions (
                resource_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                content_sha256 TEXT NOT NULL,
                parent_version INTEGER,
                created_at TEXT NOT NULL,
                PRIMARY KEY(resource_id, version)
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS resource_heads (
                resource_id TEXT PRIMARY KEY,
                version INTEGER NOT NULL,
                content_sha256 TEXT NOT NULL
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS resource_conflicts (
                conflict_id TEXT PRIMARY KEY,
                resource_id TEXT NOT NULL,
                expected_version INTEGER NOT NULL,
                expected_sha256 TEXT NOT NULL,
                actual_version INTEGER NOT NULL,
                actual_sha256 TEXT NOT NULL,
                action TEXT NOT NULL,
                created_at TEXT NOT NULL
            )""")

    def initialize(self, resource_id: str, content: object) -> ResourceVersion:
        if not resource_id:
            raise ValueError("resource_id must not be empty")
        content_sha = _sha256(content)
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.path, isolation_level=None) as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM resource_heads WHERE resource_id=?", (resource_id,)).fetchone():
                raise ValueError(f"resource already exists: {resource_id}")
            db.execute("INSERT INTO resource_versions VALUES (?,?,?,?,?)",
                       (resource_id, 1, content_sha, None, now))
            db.execute("INSERT INTO resource_heads VALUES (?,?,?)",
                       (resource_id, 1, content_sha))
        return ResourceVersion(resource_id, 1, content_sha, None, now)

    def head(self, resource_id: str) -> ResourceVersion:
        with sqlite3.connect(self.path) as db:
            row = db.execute("""SELECT v.resource_id,v.version,v.content_sha256,v.parent_version,v.created_at
                FROM resource_versions v JOIN resource_heads h
                ON h.resource_id=v.resource_id AND h.version=v.version
                WHERE v.resource_id=?""", (resource_id,)).fetchone()
        if row is None:
            raise KeyError(resource_id)
        return ResourceVersion(*row)

    def update(
        self, resource_id: str, *, expected_version: int, expected_sha256: str,
        content: object, on_reject: Callable[[ConflictEvidence], None] | None = None,
    ) -> ResourceVersion:
        if expected_version < 1 or not expected_sha256:
            raise ValueError("expected version and SHA are required")
        new_sha = _sha256(content)
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.path, isolation_level=None) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT version,content_sha256 FROM resource_heads WHERE resource_id=?",
                             (resource_id,)).fetchone()
            if row is None:
                raise KeyError(resource_id)
            actual_version, actual_sha = row
            if actual_version != expected_version or actual_sha != expected_sha256:
                evidence = ConflictEvidence(
                    uuid.uuid4().hex, resource_id, expected_version, expected_sha256,
                    actual_version, actual_sha, "UPDATE_REJECTED"
                )
                db.execute("INSERT INTO resource_conflicts VALUES (?,?,?,?,?,?,?,?)",
                           (evidence.conflict_id, resource_id, expected_version, expected_sha256,
                            actual_version, actual_sha, evidence.action, now))
                db.commit()
                if on_reject:
                    on_reject(evidence)
                raise ResourceConflictError(evidence)
            next_version = actual_version + 1
            db.execute("INSERT INTO resource_versions VALUES (?,?,?,?,?)",
                       (resource_id, next_version, new_sha, actual_version, now))
            db.execute("UPDATE resource_heads SET version=?,content_sha256=? WHERE resource_id=?",
                       (next_version, new_sha, resource_id))
        return ResourceVersion(resource_id, next_version, new_sha, actual_version, now)

    def branch(self, resource_id: str, *, parent_version: int, content: object) -> ResourceVersion:
        content_sha = _sha256(content)
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.path, isolation_level=None) as db:
            db.execute("BEGIN IMMEDIATE")
            if not db.execute("SELECT 1 FROM resource_versions WHERE resource_id=? AND version=?",
                              (resource_id, parent_version)).fetchone():
                raise KeyError((resource_id, parent_version))
            version = db.execute("SELECT COALESCE(MAX(version),0)+1 FROM resource_versions WHERE resource_id=?",
                                 (resource_id,)).fetchone()[0]
            db.execute("INSERT INTO resource_versions VALUES (?,?,?,?,?)",
                       (resource_id, version, content_sha, parent_version, now))
        return ResourceVersion(resource_id, version, content_sha, parent_version, now)

    def list_conflicts(self, resource_id: str) -> tuple[ConflictEvidence, ...]:
        with sqlite3.connect(self.path) as db:
            rows = db.execute("""SELECT conflict_id,resource_id,expected_version,expected_sha256,
                actual_version,actual_sha256,action FROM resource_conflicts
                WHERE resource_id=? ORDER BY created_at""", (resource_id,)).fetchall()
        return tuple(ConflictEvidence(*row) for row in rows)


def release_and_reconcile_on_conflict(
    evidence: ConflictEvidence, *,
    release_resources: Callable[[], None],
    reconcile_delivery: Callable[[ConflictEvidence], None],
) -> None:
    release_resources()
    reconcile_delivery(evidence)
