from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


RESOURCE_CHANGE_EVENT_SCHEMA = "RESEARCH_OS_RESOURCE_CHANGE_EVENT_V1"

ChangeOperation = Literal["CREATE", "MODIFY", "DELETE"]


@dataclass(frozen=True)
class ResourceChangeEvent:
    path: str
    operation: ChangeOperation
    source: str = "unknown"

    def __post_init__(self) -> None:
        path = str(self.path).replace("\\", "/").strip()
        operation = str(self.operation).strip().upper()
        source = str(self.source).strip() or "unknown"

        if not path:
            raise ValueError("RESOURCE_CHANGE_PATH_REQUIRED")

        if operation not in {"CREATE", "MODIFY", "DELETE"}:
            raise ValueError(
                f"RESOURCE_CHANGE_INVALID_OPERATION:{operation}"
            )

        object.__setattr__(self, "path", path)
        object.__setattr__(self, "operation", operation)
        object.__setattr__(self, "source", source)

    def to_dict(self) -> dict:
        return {
            "schema": RESOURCE_CHANGE_EVENT_SCHEMA,
            "path": self.path,
            "operation": self.operation,
            "source": self.source,
        }
