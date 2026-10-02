from __future__ import annotations

from collections.abc import Iterable

from tools.research_os_resource_change_event import ResourceChangeEvent


RESOURCE_CHANGE_COALESCER_SCHEMA = (
    "RESEARCH_OS_RESOURCE_CHANGE_COALESCER_V1"
)


class ResourceChangeCoalescer:
    """Pure deterministic batch coalescer.

    This layer does not:
    - allocate resource IDs
    - read files
    - calculate hashes
    - mutate manifests
    - perform semantic binding
    - authorize execution

    It only converts raw change events into the minimal deterministic
    set of changes that downstream incremental processing must inspect.
    """

    def coalesce(
        self,
        events: Iterable[ResourceChangeEvent],
    ) -> list[ResourceChangeEvent]:
        state: dict[str, ResourceChangeEvent] = {}

        for event in events:
            if not isinstance(event, ResourceChangeEvent):
                raise TypeError("RESOURCE_CHANGE_EVENT_REQUIRED")

            previous = state.get(event.path)

            if previous is None:
                state[event.path] = event
                continue

            operation = self._merge(
                previous.operation,
                event.operation,
            )

            if operation is None:
                state.pop(event.path, None)
                continue

            state[event.path] = ResourceChangeEvent(
                path=event.path,
                operation=operation,
                source=event.source,
            )

        return [
            state[path]
            for path in sorted(state)
        ]

    @staticmethod
    def _merge(
        previous: str,
        current: str,
    ) -> str | None:
        if previous == "CREATE" and current == "DELETE":
            return None

        if previous == "CREATE" and current == "MODIFY":
            return "CREATE"

        if previous == "MODIFY" and current == "MODIFY":
            return "MODIFY"

        if previous == "MODIFY" and current == "DELETE":
            return "DELETE"

        if previous == "DELETE" and current == "CREATE":
            return "CREATE"

        if previous == "DELETE" and current == "DELETE":
            return "DELETE"

        return current
