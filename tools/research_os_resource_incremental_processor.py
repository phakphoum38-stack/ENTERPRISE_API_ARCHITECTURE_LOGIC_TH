from __future__ import annotations

from collections.abc import Mapping, Sequence

from tools.research_os_resource_change_event import ResourceChangeEvent
from tools.research_os_resource_instance import (
    ResourceInstance,
    instance_from_file,
)


RESOURCE_INCREMENTAL_PROCESSOR_SCHEMA = (
    "RESEARCH_OS_RESOURCE_INCREMENTAL_PROCESSOR_V1"
)


class ResourceIncrementalProcessor:
    """Process only resources affected by a coalesced change batch.

    Resource identity remains external to this processor.
    The processor never allocates or invents resource IDs.
    """

    def __init__(
        self,
        resource_ids_by_path: Mapping[str, str],
    ) -> None:
        self._resource_ids_by_path = {
            _normalize_path(path): _require_resource_id(resource_id)
            for path, resource_id in resource_ids_by_path.items()
        }

    def process(
        self,
        events: Sequence[ResourceChangeEvent],
    ) -> list[dict]:
        results: list[dict] = []

        for event in events:
            if not isinstance(event, ResourceChangeEvent):
                raise TypeError("RESOURCE_CHANGE_EVENT_REQUIRED")

            path = _normalize_path(event.path)

            if event.operation == "DELETE":
                resource_id = self._resource_ids_by_path.get(path)

                if resource_id is None:
                    raise ValueError(
                        f"RESOURCE_INCREMENTAL_DELETE_ID_UNKNOWN:{path}"
                    )

                results.append(
                    {
                        "schema": RESOURCE_INCREMENTAL_PROCESSOR_SCHEMA,
                        "operation": "DELETE",
                        "path": path,
                        "resource_id": resource_id,
                        "instance": None,
                    }
                )
                continue

            resource_id = self._resource_ids_by_path.get(path)

            if resource_id is None:
                raise ValueError(
                    f"RESOURCE_INCREMENTAL_RESOURCE_ID_REQUIRED:{path}"
                )

            instance = instance_from_file(
                resource_id=resource_id,
                path=path,
            )

            results.append(
                {
                    "schema": RESOURCE_INCREMENTAL_PROCESSOR_SCHEMA,
                    "operation": event.operation,
                    "path": path,
                    "resource_id": resource_id,
                    "instance": instance,
                }
            )

        return sorted(
            results,
            key=lambda item: (
                item["path"],
                item["operation"],
                item["resource_id"],
            ),
        )


def _normalize_path(path: str) -> str:
    value = str(path).replace("\\", "/").strip()

    if not value:
        raise ValueError(
            "RESOURCE_INCREMENTAL_PATH_REQUIRED"
        )

    return value


def _require_resource_id(resource_id: str) -> str:
    value = str(resource_id).strip()

    if not value:
        raise ValueError(
            "RESOURCE_INCREMENTAL_RESOURCE_ID_REQUIRED"
        )

    return value
