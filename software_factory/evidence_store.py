from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .control_plane import EvidenceRecord


class JsonlEvidenceStore:
    """Append-only persistent evidence store using JSON Lines."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def append(self, record: EvidenceRecord) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(record), ensure_ascii=False, sort_keys=True) + "\n")

    def read_all(self) -> tuple[EvidenceRecord, ...]:
        if not self.path.exists():
            return ()
        records: list[EvidenceRecord] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                records.append(EvidenceRecord(**json.loads(line)))
        return tuple(records)
