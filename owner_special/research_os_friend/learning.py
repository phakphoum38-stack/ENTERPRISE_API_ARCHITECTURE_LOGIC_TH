from __future__ import annotations

import hashlib
import json
import os
import threading
from dataclasses import asdict, dataclass
from pathlib import Path


STATES = ("candidate", "validated", "reusable", "rejected")


@dataclass(frozen=True)
class LearningRecord:
    record_id: str
    owner_id: str
    skill_id: str
    trigger: str
    decision_source: str
    tools_used: tuple[str, ...]
    source_commit: str
    source_workflow_run: str
    changed_files: tuple[str, ...]
    validation_result: str
    pr_reference: str
    verification_timestamp: str
    confidence: float
    state: str = "candidate"
    evidence: tuple[str, ...] = ()
    version: int = 1

    def __post_init__(self) -> None:
        if self.state not in STATES:
            raise ValueError(f"invalid learning state: {self.state}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if not self.skill_id or not self.source_commit:
            raise ValueError("skill_id and source_commit are required")

    @property
    def fingerprint(self) -> str:
        payload = json.dumps(asdict(self), ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class PersistentLearningStore:
    """Append-safe, owner-scoped learning records with atomic JSON persistence.

    Learning never mutates core skills. Only records explicitly promoted to
    ``reusable`` are eligible for automatic reuse by a future learner.
    """

    schema_version = 1

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._lock = threading.RLock()
        self._records: list[LearningRecord] = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != self.schema_version:
            raise ValueError("invalid learning store schema")
        self._records = [self._from_dict(item) for item in payload.get("records", [])]

    @staticmethod
    def _from_dict(item: dict) -> LearningRecord:
        item = dict(item)
        item["tools_used"] = tuple(item.get("tools_used", ()))
        item["changed_files"] = tuple(item.get("changed_files", ()))
        item["evidence"] = tuple(item.get("evidence", ()))
        return LearningRecord(**item)

    def _flush(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": self.schema_version,
            "records": [asdict(record) for record in self._records],
        }
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, self.path)

    def add(self, record: LearningRecord) -> None:
        with self._lock:
            if any(existing.record_id == record.record_id for existing in self._records):
                raise ValueError(f"duplicate learning record: {record.record_id}")
            self._records.append(record)
            self._flush()

    def promote(self, record_id: str, state: str, *, evidence: tuple[str, ...] = ()) -> LearningRecord:
        if state not in STATES:
            raise ValueError(f"invalid learning state: {state}")
        with self._lock:
            for index, record in enumerate(self._records):
                if record.record_id == record_id:
                    if state == "reusable" and record.validation_result.lower() not in {"pass", "passed", "success", "validated"}:
                        raise ValueError("only validated evidence can become reusable")
                    updated = LearningRecord(
                        **{**asdict(record), "tools_used": tuple(record.tools_used), "changed_files": tuple(record.changed_files), "evidence": tuple(evidence or record.evidence), "state": state, "version": record.version + 1}
                    )
                    self._records[index] = updated
                    self._flush()
                    return updated
        raise KeyError(record_id)

    def reusable(self, *, owner_id: str, skill_id: str | None = None) -> tuple[LearningRecord, ...]:
        with self._lock:
            return tuple(
                record for record in self._records
                if record.owner_id == owner_id
                and record.state == "reusable"
                and (skill_id is None or record.skill_id == skill_id)
            )

    def count(self) -> int:
        with self._lock:
            return len(self._records)
