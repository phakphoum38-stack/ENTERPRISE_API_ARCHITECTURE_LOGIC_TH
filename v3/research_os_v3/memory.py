from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .storage import DataLayout
from .user_context import UserContext

_TOKEN_RE = re.compile(r"[\w\u0E00-\u0E7F]+", re.UNICODE)


@dataclass(frozen=True)
class MemoryRecord:
    id: str
    text: str
    created_at: str
    tags: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "text": self.text,
            "created_at": self.created_at,
            "tags": list(self.tags),
        }


class MemoryStore:
    """Durable per-user memory with deterministic local retrieval."""

    def __init__(self, data_layout: DataLayout) -> None:
        self.data_layout = data_layout

    def _path(self, context: UserContext) -> Path:
        layout = self.data_layout.for_user(context).ensure()
        return layout.database / "memory.jsonl"

    def add(
        self,
        context: UserContext,
        text: str,
        *,
        tags: tuple[str, ...] = (),
    ) -> MemoryRecord:
        cleaned = text.strip()
        if not cleaned:
            raise ValueError("memory text must not be empty")
        record = MemoryRecord(
            id=uuid4().hex,
            text=cleaned,
            created_at=datetime.now(timezone.utc).isoformat(),
            tags=tuple(tag.strip() for tag in tags if tag.strip()),
        )
        path = self._path(context)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
        return record

    def list(self, context: UserContext, *, limit: int = 100) -> list[MemoryRecord]:
        path = self._path(context)
        if not path.exists():
            return []
        records: list[MemoryRecord] = []
        with path.open("r", encoding="utf-8") as stream:
            for line in stream:
                line = line.strip()
                if not line:
                    continue
                try:
                    raw = json.loads(line)
                    records.append(
                        MemoryRecord(
                            id=str(raw["id"]),
                            text=str(raw["text"]),
                            created_at=str(raw["created_at"]),
                            tags=tuple(str(tag) for tag in raw.get("tags", [])),
                        )
                    )
                except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                    continue
        return records[-max(1, min(limit, 1000)) :]

    def search(
        self,
        context: UserContext,
        query: str,
        *,
        limit: int = 8,
    ) -> list[MemoryRecord]:
        wanted = self._tokens(query)
        if not wanted:
            return []
        scored: list[tuple[int, MemoryRecord]] = []
        for record in self.list(context, limit=1000):
            haystack = self._tokens(record.text + " " + " ".join(record.tags))
            score = len(wanted & haystack)
            if score:
                scored.append((score, record))
        scored.sort(key=lambda item: (item[0], item[1].created_at), reverse=True)
        return [record for _, record in scored[: max(1, min(limit, 50))]]

    @staticmethod
    def _tokens(value: str) -> set[str]:
        return {token.lower() for token in _TOKEN_RE.findall(value) if len(token) > 1}
