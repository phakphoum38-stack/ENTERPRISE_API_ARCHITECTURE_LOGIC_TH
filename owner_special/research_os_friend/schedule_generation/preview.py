from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .models import GenerationResult


class PreviewNotFoundError(KeyError):
    """Raised when a preview is not present in the requested scope."""


@dataclass(frozen=True)
class SchedulePreview:
    preview_id: str
    owner_id: str
    profile_id: str
    session_id: str
    status: str
    created_at: str
    result: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "preview_id": self.preview_id,
            "owner_id": self.owner_id,
            "profile_id": self.profile_id,
            "session_id": self.session_id,
            "status": self.status,
            "created_at": self.created_at,
            "result": self.result,
        }


class SchedulePreviewStore:
    """Persistent owner/profile/session scoped schedule preview store."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self._lock = threading.RLock()

    def create(
        self,
        *,
        owner_id: str,
        profile_id: str,
        session_id: str,
        result: GenerationResult,
    ) -> SchedulePreview:
        preview_id = uuid4().hex
        preview = SchedulePreview(
            preview_id=preview_id,
            owner_id=owner_id,
            profile_id=profile_id,
            session_id=session_id,
            status="pending",
            created_at=datetime.now(timezone.utc).isoformat(),
            result=dict(result),
        )
        with self._lock:
            self._write(preview)
        return preview

    def get(
        self,
        *,
        owner_id: str,
        profile_id: str,
        session_id: str,
        preview_id: str,
    ) -> SchedulePreview:
        with self._lock:
            path = self._path(owner_id, profile_id, session_id, preview_id)
            if not path.exists():
                raise PreviewNotFoundError("preview not found")
            payload = json.loads(path.read_text(encoding="utf-8"))

        preview = SchedulePreview(
            preview_id=str(payload["preview_id"]),
            owner_id=str(payload["owner_id"]),
            profile_id=str(payload["profile_id"]),
            session_id=str(payload["session_id"]),
            status=str(payload["status"]),
            created_at=str(payload["created_at"]),
            result=dict(payload["result"]),
        )

        if (
            preview.owner_id != owner_id
            or preview.profile_id != profile_id
            or preview.session_id != session_id
            or preview.preview_id != preview_id
        ):
            raise PermissionError("preview scope rejected")

        return preview

    def confirm(
        self,
        *,
        owner_id: str,
        profile_id: str,
        session_id: str,
        preview_id: str,
    ) -> SchedulePreview:
        with self._lock:
            preview = self.get(
                owner_id=owner_id,
                profile_id=profile_id,
                session_id=session_id,
                preview_id=preview_id,
            )

            if preview.status != "pending":
                raise ValueError(
                    f"preview cannot be confirmed from status: {preview.status}"
                )

            confirmed = SchedulePreview(
                preview_id=preview.preview_id,
                owner_id=preview.owner_id,
                profile_id=preview.profile_id,
                session_id=preview.session_id,
                status="confirmed",
                created_at=preview.created_at,
                result=preview.result,
            )
            self._write(confirmed)
            return confirmed

    def _path(
        self,
        owner_id: str,
        profile_id: str,
        session_id: str,
        preview_id: str,
    ) -> Path:
        return (
            self.root
            / "owners"
            / owner_id
            / "schedule_previews"
            / profile_id
            / session_id
            / f"{preview_id}.json"
        )

    def _write(self, preview: SchedulePreview) -> None:
        path = self._path(
            preview.owner_id,
            preview.profile_id,
            preview.session_id,
            preview.preview_id,
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(
                preview.to_dict(),
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, path)
