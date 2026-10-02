import unittest

from tools.research_os_resource_change_coalescer import (
    RESOURCE_CHANGE_COALESCER_SCHEMA,
    ResourceChangeCoalescer,
)
from tools.research_os_resource_change_event import ResourceChangeEvent


class ResourceChangeCoalescerTests(unittest.TestCase):

    def setUp(self):
        self.coalescer = ResourceChangeCoalescer()

    def event(self, path, operation):
        return ResourceChangeEvent(
            path=path,
            operation=operation,
            source="flutter",
        )

    def test_schema_exists(self):
        self.assertEqual(
            RESOURCE_CHANGE_COALESCER_SCHEMA,
            "RESEARCH_OS_RESOURCE_CHANGE_COALESCER_V1",
        )

    def test_empty_batch(self):
        self.assertEqual(
            self.coalescer.coalesce([]),
            [],
        )

    def test_single_event_survives(self):
        result = self.coalescer.coalesce([
            self.event("lib/a.dart", "MODIFY"),
        ])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].path, "lib/a.dart")
        self.assertEqual(result[0].operation, "MODIFY")

    def test_create_modify_remains_create(self):
        result = self.coalescer.coalesce([
            self.event("lib/a.dart", "CREATE"),
            self.event("lib/a.dart", "MODIFY"),
            self.event("lib/a.dart", "MODIFY"),
        ])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].operation, "CREATE")

    def test_modify_burst_collapses(self):
        result = self.coalescer.coalesce([
            self.event("lib/a.dart", "MODIFY"),
            self.event("lib/a.dart", "MODIFY"),
            self.event("lib/a.dart", "MODIFY"),
            self.event("lib/a.dart", "MODIFY"),
            self.event("lib/a.dart", "MODIFY"),
        ])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].operation, "MODIFY")

    def test_create_delete_cancels(self):
        result = self.coalescer.coalesce([
            self.event("lib/generated.dart", "CREATE"),
            self.event("lib/generated.dart", "MODIFY"),
            self.event("lib/generated.dart", "DELETE"),
        ])

        self.assertEqual(result, [])

    def test_modify_delete_becomes_delete(self):
        result = self.coalescer.coalesce([
            self.event("lib/a.dart", "MODIFY"),
            self.event("lib/a.dart", "DELETE"),
        ])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].operation, "DELETE")

    def test_delete_create_becomes_create(self):
        result = self.coalescer.coalesce([
            self.event("lib/a.dart", "DELETE"),
            self.event("lib/a.dart", "CREATE"),
        ])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].operation, "CREATE")

    def test_paths_are_deterministically_sorted(self):
        result = self.coalescer.coalesce([
            self.event("z.dart", "MODIFY"),
            self.event("a.dart", "MODIFY"),
            self.event("m.dart", "MODIFY"),
        ])

        self.assertEqual(
            [item.path for item in result],
            [
                "a.dart",
                "m.dart",
                "z.dart",
            ],
        )

    def test_does_not_create_resource_id(self):
        result = self.coalescer.coalesce([
            self.event("lib/a.dart", "MODIFY"),
        ])

        self.assertFalse(
            hasattr(result[0], "resource_id")
        )

    def test_repeated_batches_are_identical(self):
        events = [
            self.event("lib/z.dart", "MODIFY"),
            self.event("lib/a.dart", "CREATE"),
            self.event("lib/a.dart", "MODIFY"),
            self.event("lib/m.dart", "DELETE"),
        ]

        first = self.coalescer.coalesce(events)
        second = self.coalescer.coalesce(events)

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
