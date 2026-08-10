from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SECRET_RE = re.compile(r"(?i)(sk-[A-Za-z0-9_-]{12,}|Bearer\s+[A-Za-z0-9._-]{12,})")


def redact(value: str) -> str:
    return _SECRET_RE.sub("[REDACTED]", value)


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    timestamp: str
    owner_id: str
    profile_id: str
    session_id: str
    event: str
    data: dict[str, Any]


class EvidenceRecorder:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self.records: list[EvidenceRecord] = []

    def record(
        self,
        *,
        owner_id: str,
        profile_id: str,
        session_id: str,
        event: str,
        data: dict[str, Any],
    ) -> str:
        sanitized = json.loads(redact(json.dumps(data, sort_keys=True)))
        record = EvidenceRecord(
            evidence_id=uuid.uuid4().hex,
            timestamp=datetime.now(timezone.utc).isoformat(),
            owner_id=owner_id,
            profile_id=profile_id,
            session_id=session_id,
            event=event,
            data=sanitized,
        )
        self.records.append(record)
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(asdict(record), sort_keys=True) + "\n")
        return record.evidence_id
