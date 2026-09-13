from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterable

from .approval import ApprovalRecord, ApprovalState


class PersistentApprovalStore:
    """Owner-scoped atomic JSON persistence for explicit approval records."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _encode(record: ApprovalRecord) -> dict[str, object]:
        return {
            "approval_id": record.approval_id,
            "owner_id": record.owner_id,
            "profile_id": record.profile_id,
            "session_id": record.session_id,
            "tool_name": record.tool_name,
            "request_fingerprint": record.request_fingerprint,
            "state": record.state.value,
            "created_at": record.created_at,
            "decided_at": record.decided_at,
            "reason": record.reason,
        }

    @staticmethod
    def _decode(payload: dict[str, object]) -> ApprovalRecord:
        return ApprovalRecord(
            approval_id=str(payload["approval_id"]),
            owner_id=str(payload["owner_id"]),
            profile_id=str(payload["profile_id"]),
            session_id=str(payload["session_id"]),
            tool_name=str(payload["tool_name"]),
            request_fingerprint=str(payload["request_fingerprint"]),
            state=ApprovalState(str(payload["state"])),
            created_at=str(payload["created_at"]),
            decided_at=None if payload.get("decided_at") is None else str(payload["decided_at"]),
            reason=str(payload.get("reason", "")),
        )

    def load(self) -> tuple[ApprovalRecord, ...]:
        if not self.path.is_file():
            return ()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("approval store root must be an object")
        records = payload.get("records", [])
        if not isinstance(records, list):
            raise ValueError("approval store records must be a list")
        decoded = tuple(self._decode(item) for item in records if isinstance(item, dict))
        return tuple(sorted(decoded, key=lambda item: (item.created_at, item.approval_id)))

    def save(self, records: Iterable[ApprovalRecord]) -> None:
        encoded = {
            "version": 1,
            "records": [self._encode(record) for record in sorted(records, key=lambda item: (item.created_at, item.approval_id))],
        }
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=self.path.parent,
            prefix=f".{self.path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            json.dump(encoded, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.replace(temporary, self.path)
        finally:
            if temporary.exists():
                temporary.unlink()
