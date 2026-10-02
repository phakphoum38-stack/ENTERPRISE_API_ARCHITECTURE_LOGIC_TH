from __future__ import annotations

from collections import OrderedDict

from tools.research_os_resource_change_event import ResourceChangeEvent


RESOURCE_CHANGE_QUEUE_SCHEMA = "RESEARCH_OS_RESOURCE_CHANGE_QUEUE_V1"


class ResourceChangeQueue:
    def __init__(self) -> None:
        self._events: OrderedDict[str, ResourceChangeEvent] = OrderedDict()

    def push(self, event: ResourceChangeEvent) -> None:
        if not isinstance(event, ResourceChangeEvent):
            raise TypeError("RESOURCE_CHANGE_EVENT_REQUIRED")

        existing = self._events.get(event.path)

        if existing is None:
            self._events[event.path] = event
            return

        operation = _coalesce_operations(
            existing.operation,
            event.operation,
        )

        if operation is None:
            self._events.pop(event.path, None)
            return

        self._events[event.path] = ResourceChangeEvent(
            path=event.path,
            operation=operation,
            source=event.source,
        )

    def extend(self, events) -> None:
        for event in events:
            self.push(event)

    def drain(self) -> list[ResourceChangeEvent]:
        events = [
            self._events[path]
            for path in sorted(self._events)
        ]
        self._events.clear()
        return events

    def snapshot(self) -> list[ResourceChangeEvent]:
        return [
            self._events[path]
            for path in sorted(self._events)
        ]

    def __len__(self) -> int:
        return len(self._events)


def _coalesce_operations(old: str, new: str) -> str | None:
    if old == "CREATE" and new == "DELETE":
        return None

    if old == "CREATE" and new == "MODIFY":
        return "CREATE"

    if old == "MODIFY" and new == "MODIFY":
        return "MODIFY"

    if old == "MODIFY" and new == "DELETE":
        return "DELETE"

    if old == "DELETE" and new == "CREATE":
        return "CREATE"

    if old == "DELETE" and new == "DELETE":
        return "DELETE"

    return new
