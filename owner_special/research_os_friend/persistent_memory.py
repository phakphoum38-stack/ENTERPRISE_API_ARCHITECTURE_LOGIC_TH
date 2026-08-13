from __future__ import annotations

import json
import os
import threading
from dataclasses import asdict
from pathlib import Path

from .memory import MemoryItem, ScopedMemory


class PersistentScopedMemory(ScopedMemory):
    """Atomic owner/profile/session scoped memory persisted as local JSON."""

    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = Path(path)
        self._lock = threading.RLock()
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != 1 or not isinstance(payload.get("items"), list):
            raise ValueError("invalid persistent memory file")
        loaded: list[MemoryItem] = []
        for item in payload["items"]:
            loaded.append(
                MemoryItem(
                    owner_id=str(item["owner_id"]),
                    profile_id=str(item["profile_id"]),
                    session_id=str(item["session_id"]),
                    kind=str(item["kind"]),
                    text=str(item["text"]),
                )
            )
        self._items = loaded

    def _flush(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "items": [asdict(item) for item in self._items],
        }
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, self.path)

    def remember(
        self,
        *,
        owner_id: str,
        profile_id: str,
        session_id: str,
        kind: str,
        text: str,
    ) -> None:
        with self._lock:
            super().remember(
                owner_id=owner_id,
                profile_id=profile_id,
                session_id=session_id,
                kind=kind,
                text=text,
            )
            self._flush()

    def recall(self, *, owner_id: str, profile_id: str, session_id: str) -> tuple[MemoryItem, ...]:
        with self._lock:
            return super().recall(owner_id=owner_id, profile_id=profile_id, session_id=session_id)

    def count(self) -> int:
        with self._lock:
            return len(self._items)
