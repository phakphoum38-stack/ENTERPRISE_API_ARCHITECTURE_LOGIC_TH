#!/usr/bin/env python3
"""Local-first structured memory engine for Research OS.

This module complements ``memory.py``. The legacy module indexes curated Markdown
artifacts; this engine manages structured runtime memories for conversations,
projects, preferences, knowledge, and files without changing the existing
retrieval contract.
"""

from __future__ import annotations

import json
import os
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_tags(values: Iterable[str]) -> list[str]:
    return sorted({str(value).strip().lower() for value in values if str(value).strip()})


@dataclass(frozen=True)
class MemoryRecord:
    id: str
    type: str
    content: str
    created_at: str
    updated_at: str
    source: str = "user"
    title: str = ""
    project_id: str | None = None
    session_id: str | None = None
    provider: str | None = None
    tags: list[str] = field(default_factory=list)
    priority: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        type: str,
        content: str,
        title: str = "",
        source: str = "user",
        project_id: str | None = None,
        session_id: str | None = None,
        provider: str | None = None,
        tags: Iterable[str] = (),
        priority: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> "MemoryRecord":
        body = content.strip()
        if not body:
            raise ValueError("memory content is required")
        memory_type = type.strip().lower()
        if not memory_type:
            raise ValueError("memory type is required")
        now = _utc_now()
        return cls(
            id=f"mem_{uuid.uuid4().hex}",
            type=memory_type,
            content=body,
            title=title.strip(),
            source=source.strip().lower() or "user",
            created_at=now,
            updated_at=now,
            project_id=project_id,
            session_id=session_id,
            provider=provider,
            tags=_normalize_tags(tags),
            priority=max(-100, min(int(priority), 100)),
            metadata=dict(metadata or {}),
        )


@dataclass(frozen=True)
class MemorySearchHit:
    record: MemoryRecord
    score: int
    matched_terms: list[str]


class JsonMemoryStore:
    """Small dependency-free JSON store with atomic replacement writes."""

    def __init__(self, path: Path | None = None):
        if path is None:
            configured = os.getenv("RESEARCH_OS_MEMORY_STORE", "").strip()
            if configured:
                path = Path(configured).expanduser()
            else:
                data_dir = Path(os.getenv("RESEARCH_OS_DATA_DIR", Path.home() / ".research_os"))
                path = data_dir / "memory" / "records.json"
        self.path = path
        self._lock = threading.RLock()

    def _load_raw(self) -> list[dict[str, Any]]:
        if not self.path.is_file():
            return []
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"cannot read memory store: {exc}") from exc
        if not isinstance(value, list):
            raise RuntimeError("memory store root must be a list")
        return [item for item in value if isinstance(item, dict)]

    def _save_raw(self, rows: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temporary.replace(self.path)

    @staticmethod
    def _decode(row: dict[str, Any]) -> MemoryRecord:
        return MemoryRecord(
            id=str(row["id"]),
            type=str(row["type"]),
            content=str(row["content"]),
            title=str(row.get("title", "")),
            source=str(row.get("source", "user")),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
            project_id=row.get("project_id"),
            session_id=row.get("session_id"),
            provider=row.get("provider"),
            tags=_normalize_tags(row.get("tags", [])),
            priority=int(row.get("priority", 0)),
            metadata=dict(row.get("metadata", {})),
        )

    def list(self) -> list[MemoryRecord]:
        with self._lock:
            records = [self._decode(row) for row in self._load_raw()]
        records.sort(key=lambda item: (item.updated_at, item.id), reverse=True)
        return records

    def get(self, memory_id: str) -> MemoryRecord | None:
        for record in self.list():
            if record.id == memory_id:
                return record
        return None

    def save(self, record: MemoryRecord) -> MemoryRecord:
        with self._lock:
            rows = self._load_raw()
            replaced = False
            for index, row in enumerate(rows):
                if str(row.get("id")) == record.id:
                    rows[index] = asdict(record)
                    replaced = True
                    break
            if not replaced:
                rows.append(asdict(record))
            self._save_raw(rows)
        return record

    def update(self, memory_id: str, **changes: Any) -> MemoryRecord:
        current = self.get(memory_id)
        if current is None:
            raise KeyError(memory_id)
        allowed = {
            "type",
            "content",
            "title",
            "source",
            "project_id",
            "session_id",
            "provider",
            "tags",
            "priority",
            "metadata",
        }
        unknown = set(changes) - allowed
        if unknown:
            raise ValueError(f"unsupported memory fields: {sorted(unknown)}")
        values = asdict(current)
        values.update(changes)
        values["content"] = str(values["content"]).strip()
        if not values["content"]:
            raise ValueError("memory content is required")
        values["type"] = str(values["type"]).strip().lower()
        values["tags"] = _normalize_tags(values.get("tags", []))
        values["priority"] = max(-100, min(int(values.get("priority", 0)), 100))
        values["metadata"] = dict(values.get("metadata", {}))
        values["updated_at"] = _utc_now()
        updated = MemoryRecord(**values)
        return self.save(updated)

    def delete(self, memory_id: str) -> bool:
        with self._lock:
            rows = self._load_raw()
            kept = [row for row in rows if str(row.get("id")) != memory_id]
            if len(kept) == len(rows):
                return False
            self._save_raw(kept)
            return True


class MemoryEngine:
    def __init__(self, store: JsonMemoryStore | None = None):
        self.store = store or JsonMemoryStore()

    @staticmethod
    def _terms(value: str) -> set[str]:
        import re

        return {
            token.lower()
            for token in re.findall(r"[A-Za-z0-9_\-]+|[\u0E00-\u0E7F]+", value)
            if len(token.strip()) >= 2
        }

    def remember(self, **kwargs: Any) -> MemoryRecord:
        return self.store.save(MemoryRecord.create(**kwargs))

    def search(
        self,
        query: str,
        *,
        limit: int = 10,
        type: str | None = None,
        project_id: str | None = None,
        session_id: str | None = None,
        tags: Iterable[str] = (),
    ) -> list[MemorySearchHit]:
        terms = self._terms(query)
        required_tags = set(_normalize_tags(tags))
        hits: list[MemorySearchHit] = []
        for record in self.store.list():
            if type and record.type != type.strip().lower():
                continue
            if project_id and record.project_id != project_id:
                continue
            if session_id and record.session_id != session_id:
                continue
            if required_tags and not required_tags.issubset(set(record.tags)):
                continue
            haystack = " ".join([record.title, record.content, " ".join(record.tags)])
            memory_terms = self._terms(haystack)
            matched = terms & memory_terms
            if terms and not matched:
                continue
            score = len(matched) * 10 + record.priority
            if record.title and terms & self._terms(record.title):
                score += 10
            hits.append(MemorySearchHit(record=record, score=score, matched_terms=sorted(matched)))
        hits.sort(key=lambda item: (-item.score, item.record.updated_at, item.record.id))
        return hits[: max(1, min(int(limit), 100))]

    def timeline(
        self,
        *,
        project_id: str | None = None,
        session_id: str | None = None,
        limit: int = 100,
    ) -> list[MemoryRecord]:
        records = self.store.list()
        if project_id:
            records = [item for item in records if item.project_id == project_id]
        if session_id:
            records = [item for item in records if item.session_id == session_id]
        records.sort(key=lambda item: (item.created_at, item.id), reverse=True)
        return records[: max(1, min(int(limit), 500))]
