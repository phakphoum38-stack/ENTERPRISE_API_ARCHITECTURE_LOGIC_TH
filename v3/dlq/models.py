from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping


class DLQStatus(str, Enum):
    AVAILABLE = "available"
    REPLAYING = "replaying"
    REPLAYED = "replayed"
    REJECTED = "rejected"


@dataclass(frozen=True)
class DLQRecord:
    task_id: str
    event_id: str
    delivery_id: str
    idempotency_key: str
    attempt: int
    max_attempts: int
    error_type: str
    error_message: str
    payload_reference: str
    failed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    first_failed_at: datetime | None = None
    replay_count: int = 0
    status: DLQStatus = DLQStatus.AVAILABLE
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.attempt < 1:
            raise ValueError("attempt must be >= 1")
        if self.max_attempts < self.attempt:
            raise ValueError("max_attempts must be >= attempt")
        if not self.task_id or not self.event_id or not self.idempotency_key:
            raise ValueError("task_id, event_id and idempotency_key are required")
