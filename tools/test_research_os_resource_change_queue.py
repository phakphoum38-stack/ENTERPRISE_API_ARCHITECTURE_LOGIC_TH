import unittest

from tools.research_os_resource_change_event import (
    RESOURCE_CHANGE_EVENT_SCHEMA,
    ResourceChangeEvent,
)
from tools.research_os_resource_change_queue import ResourceChangeQueue


class ResourceChangeQueueTests(unittest.TestCase):

    def event(self, path, operation):
        return ResourceChangeEvent(
            path=path,
            operation=operation,
            source="flutter",
        )

    def test_event_normalizes_path_and_operation(self):
        event = self.event(r"lib\src\a.dart", "modify")

        self.assertEqual(event.path, "lib/src/a.dart")
        self.assertEqual(event.operation, "MODIFY")

    def test_event_schema_is_present(self):
        event = self.event("lib/a.dart", "CREATE")

        self.assertEqual(
            event.to_dict()["schema"],
            RESOURCE_CHANGE_EVENT_SCHEMA,
        )

    def test_invalid_operation_fails_closed(self):
        with self.assertRaises(ValueError):
            self.event("lib/a.dart", "UNKNOWN")

    def test_create_modify_collapses_to_create(self):
        queue = ResourceChangeQueue()

        queue.push(self.event("lib/a.dart", "CREATE"))
        queue.push(self.event("lib/a.dart", "MODIFY"))

        events = queue.drain()

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].operation, "CREATE")

    def test_modify_modify_collapses_to_one_modify(self):
        queue = ResourceChangeQueue()

        queue.push(self.event("lib/a.dart", "MODIFY"))
        queue.push(self.event("lib/a.dart", "MODIFY"))

        events = queue.drain()

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].operation, "MODIFY")

    def test_create_delete_cancels(self):
        queue = ResourceChangeQueue()

        queue.push(self.event("lib/a.dart", "CREATE"))
        queue.push(self.event("lib/a.dart", "DELETE"))

        self.assertEqual(queue.drain(), [])

    def test_modify_delete_becomes_delete(self):
        queue = ResourceChangeQueue()

        queue.push(self.event("lib/a.dart", "MODIFY"))
        queue.push(self.event("lib/a.dart", "DELETE"))

        events = queue.drain()

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].operation, "DELETE")

    def test_delete_create_becomes_create(self):
        queue = ResourceChangeQueue()

        queue.push(self.event("lib/a.dart", "DELETE"))
        queue.push(self.event("lib/a.dart", "CREATE"))

        events = queue.drain()

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].operation, "CREATE")

    def test_multiple_paths_are_deterministic(self):
        queue = ResourceChangeQueue()

        queue.push(self.event("lib/z.dart", "MODIFY"))
        queue.push(self.event("lib/a.dart", "CREATE"))
        queue.push(self.event("lib/m.dart", "DELETE"))

        events = queue.drain()

        self.assertEqual(
            [event.path for event in events],
            [
                "lib/a.dart",
                "lib/m.dart",
                "lib/z.dart",
            ],
        )

    def test_drain_clears_queue(self):
        queue = ResourceChangeQueue()

        queue.push(self.event("lib/a.dart", "MODIFY"))

        self.assertEqual(len(queue), 1)

        queue.drain()

        self.assertEqual(len(queue), 0)


if __name__ == "__main__":
    unittest.main()
