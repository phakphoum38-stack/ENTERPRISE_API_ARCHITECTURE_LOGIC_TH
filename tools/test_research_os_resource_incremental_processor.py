import tempfile
import unittest
from pathlib import Path

from tools.research_os_resource_change_event import ResourceChangeEvent
from tools.research_os_resource_incremental_processor import (
    RESOURCE_INCREMENTAL_PROCESSOR_SCHEMA,
    ResourceIncrementalProcessor,
)


class ResourceIncrementalProcessorTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        self.a = self.root / "a.dart"
        self.b = self.root / "b.dart"

        self.a.write_text("void main() {}\n", encoding="utf-8")
        self.b.write_text("void b() {}\n", encoding="utf-8")

        self.processor = ResourceIncrementalProcessor(
            {
                self.a: "RID-A",
                self.b: "RID-B",
            }
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def event(self, path, operation):
        return ResourceChangeEvent(
            path=str(path),
            operation=operation,
            source="flutter",
        )

    def test_schema_is_present(self):
        result = self.processor.process([
            self.event(self.a, "MODIFY"),
        ])

        self.assertEqual(
            result[0]["schema"],
            RESOURCE_INCREMENTAL_PROCESSOR_SCHEMA,
        )

    def test_modify_builds_only_affected_instance(self):
        result = self.processor.process([
            self.event(self.a, "MODIFY"),
        ])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["operation"], "MODIFY")
        self.assertEqual(result[0]["resource_id"], "RID-A")
        self.assertIsNotNone(result[0]["instance"])

    def test_create_builds_instance(self):
        result = self.processor.process([
            self.event(self.a, "CREATE"),
        ])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["operation"], "CREATE")
        self.assertEqual(result[0]["resource_id"], "RID-A")
        self.assertIsNotNone(result[0]["instance"])

    def test_delete_does_not_read_file(self):
        self.a.unlink()

        result = self.processor.process([
            self.event(self.a, "DELETE"),
        ])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["operation"], "DELETE")
        self.assertEqual(result[0]["resource_id"], "RID-A")
        self.assertIsNone(result[0]["instance"])

    def test_unknown_create_fails_closed(self):
        unknown = self.root / "new.dart"
        unknown.write_text("void newFile() {}\n", encoding="utf-8")

        with self.assertRaisesRegex(
            ValueError,
            "RESOURCE_INCREMENTAL_RESOURCE_ID_REQUIRED",
        ):
            self.processor.process([
                self.event(unknown, "CREATE"),
            ])

    def test_unknown_delete_fails_closed(self):
        unknown = self.root / "missing.dart"

        with self.assertRaisesRegex(
            ValueError,
            "RESOURCE_INCREMENTAL_DELETE_ID_UNKNOWN",
        ):
            self.processor.process([
                self.event(unknown, "DELETE"),
            ])

    def test_windows_path_is_normalized(self):
        result = self.processor.process([
            self.event(
                str(self.a).replace("/", "\\"),
                "MODIFY",
            ),
        ])

        self.assertEqual(
            result[0]["path"],
            str(self.a).replace("\\", "/"),
        )

    def test_multiple_events_are_deterministic(self):
        result = self.processor.process([
            self.event(self.b, "MODIFY"),
            self.event(self.a, "MODIFY"),
        ])

        self.assertEqual(
            [item["path"] for item in result],
            sorted([
                str(self.a).replace("\\", "/"),
                str(self.b).replace("\\", "/"),
            ]),
        )

    def test_resource_id_is_not_allocated_by_processor(self):
        unknown = self.root / "new.dart"
        unknown.write_text("new\n", encoding="utf-8")

        with self.assertRaises(ValueError):
            self.processor.process([
                self.event(unknown, "CREATE"),
            ])

        self.assertNotIn(
            str(unknown).replace("\\", "/"),
            self.processor._resource_ids_by_path,
        )


if __name__ == "__main__":
    unittest.main()
