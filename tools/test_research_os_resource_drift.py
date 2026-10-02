import unittest

from tools.research_os_resource_drift import (
    RESOURCE_DRIFT_SCHEMA,
    compare_instances,
    compare_resource_changes,
    compare_resource_sets,
)
from tools.research_os_resource_instance import ResourceInstance


def make(resource_id, path, content):
    return ResourceInstance.create(
        resource_id,
        path,
        content,
    )


class ResourceDriftTests(unittest.TestCase):

    def test_identical_instances_are_unchanged(self):
        baseline = make("R1", "tools/a.py", b"a")
        current = make("R1", "tools/a.py", b"a")

        result = compare_instances(baseline, current)

        self.assertEqual(result.state, "UNCHANGED")

    def test_content_change_is_detected(self):
        baseline = make("R1", "tools/a.py", b"a")
        current = make("R1", "tools/a.py", b"b")

        result = compare_instances(baseline, current)

        self.assertEqual(result.state, "CONTENT_DRIFT")

    def test_path_change_is_detected(self):
        baseline = make("R1", "tools/a.py", b"a")
        current = make("R1", "tools/b.py", b"a")

        result = compare_instances(baseline, current)

        self.assertEqual(result.state, "PATH_DRIFT")

    def test_resource_id_change_is_detected(self):
        baseline = make("R1", "tools/a.py", b"a")
        current = make("R2", "tools/a.py", b"a")

        result = compare_instances(baseline, current)

        self.assertEqual(result.state, "RESOURCE_ID_DRIFT")

    def test_added_resource_is_detected(self):
        result = compare_resource_sets(
            {},
            {"R1": make("R1", "tools/a.py", b"a")},
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].state, "ADDED")

    def test_removed_resource_is_detected(self):
        result = compare_resource_sets(
            {"R1": make("R1", "tools/a.py", b"a")},
            {},
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].state, "REMOVED")

    def test_results_are_deterministic(self):
        baseline = {
            "R2": make("R2", "tools/b.py", b"b"),
            "R1": make("R1", "tools/a.py", b"a"),
        }
        current = {
            "R1": make("R1", "tools/a.py", b"changed"),
            "R3": make("R3", "tools/c.py", b"c"),
        }

        first = compare_resource_sets(baseline, current)
        second = compare_resource_sets(baseline, current)

        self.assertEqual(first, second)
        self.assertEqual(
            [item.resource_id for item in first],
            ["R1", "R2", "R3"],
        )

    def test_incremental_modify_content_drift(self):
        baseline = {
            "R1": make("R1", "tools/a.py", b"a"),
        }

        changes = [
            {
                "operation": "MODIFY",
                "path": "tools/a.py",
                "resource_id": "R1",
                "instance": make("R1", "tools/a.py", b"changed"),
            }
        ]

        result = compare_resource_changes(
            baseline,
            changes,
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].resource_id, "R1")
        self.assertEqual(result[0].state, "CONTENT_DRIFT")

    def test_incremental_modify_unchanged(self):
        baseline = {
            "R1": make("R1", "tools/a.py", b"a"),
        }

        changes = [
            {
                "operation": "MODIFY",
                "path": "tools/a.py",
                "resource_id": "R1",
                "instance": make("R1", "tools/a.py", b"a"),
            }
        ]

        result = compare_resource_changes(
            baseline,
            changes,
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].state, "UNCHANGED")

    def test_incremental_create_is_added(self):
        baseline = {}

        changes = [
            {
                "operation": "CREATE",
                "path": "tools/new.py",
                "resource_id": "R2",
                "instance": make("R2", "tools/new.py", b"new"),
            }
        ]

        result = compare_resource_changes(
            baseline,
            changes,
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].resource_id, "R2")
        self.assertEqual(result[0].state, "ADDED")

    def test_incremental_delete_is_removed(self):
        baseline = {
            "R1": make("R1", "tools/a.py", b"a"),
        }

        changes = [
            {
                "operation": "DELETE",
                "path": "tools/a.py",
                "resource_id": "R1",
                "instance": None,
            }
        ]

        result = compare_resource_changes(
            baseline,
            changes,
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].resource_id, "R1")
        self.assertEqual(result[0].state, "REMOVED")

    def test_incremental_delete_requires_baseline(self):
        with self.assertRaises(ValueError):
            compare_resource_changes(
                {},
                [
                    {
                        "operation": "DELETE",
                        "path": "tools/a.py",
                        "resource_id": "R1",
                        "instance": None,
                    }
                ],
            )

    def test_incremental_resource_id_mismatch_fails_closed(self):
        with self.assertRaises(ValueError):
            compare_resource_changes(
                {
                    "R1": make("R1", "tools/a.py", b"a"),
                },
                [
                    {
                        "operation": "MODIFY",
                        "path": "tools/a.py",
                        "resource_id": "R1",
                        "instance": make(
                            "R2",
                            "tools/a.py",
                            b"changed",
                        ),
                    }
                ],
            )

    def test_incremental_requires_instance_for_non_delete(self):
        with self.assertRaises(TypeError):
            compare_resource_changes(
                {},
                [
                    {
                        "operation": "CREATE",
                        "path": "tools/new.py",
                        "resource_id": "R2",
                        "instance": None,
                    }
                ],
            )

    def test_incremental_results_are_deterministic(self):
        baseline = {
            "R2": make("R2", "tools/b.py", b"b"),
            "R1": make("R1", "tools/a.py", b"a"),
        }

        changes = [
            {
                "operation": "MODIFY",
                "path": "tools/b.py",
                "resource_id": "R2",
                "instance": make("R2", "tools/b.py", b"changed"),
            },
            {
                "operation": "MODIFY",
                "path": "tools/a.py",
                "resource_id": "R1",
                "instance": make("R1", "tools/a.py", b"changed"),
            },
        ]

        first = compare_resource_changes(
            baseline,
            changes,
        )
        second = compare_resource_changes(
            baseline,
            changes,
        )

        self.assertEqual(first, second)
        self.assertEqual(
            [item.resource_id for item in first],
            ["R1", "R2"],
        )

    def test_schema_is_present(self):
        result = compare_instances(
            make("R1", "tools/a.py", b"a"),
            make("R1", "tools/a.py", b"a"),
        )

        self.assertEqual(
            result.to_dict()["schema"],
            RESOURCE_DRIFT_SCHEMA,
        )

    def test_missing_instance_fields_fail_closed(self):
        class Broken:
            def to_dict(self):
                return {"resource_id": "R1"}

        with self.assertRaises(ValueError):
            compare_instances(Broken(), Broken())


if __name__ == "__main__":
    unittest.main()
