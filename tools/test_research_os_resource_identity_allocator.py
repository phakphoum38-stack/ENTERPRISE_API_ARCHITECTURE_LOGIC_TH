import unittest

from tools.research_os_resource_identity_allocator import (
    allocate_resource_ids,
    make_resource_id,
    make_resource_key,
)


class ResourceIdentityAllocatorTests(unittest.TestCase):

    def test_same_identity_different_paths_are_distinct(self):
        a = make_resource_key(
            "IMPLEMENTATION",
            "EXAMPLE",
            "tools/a.py",
        )
        b = make_resource_key(
            "IMPLEMENTATION",
            "EXAMPLE",
            "tools/b.py",
        )

        self.assertNotEqual(
            make_resource_id(a),
            make_resource_id(b),
        )

    def test_normalization_is_deterministic(self):
        a = make_resource_key(
            "implementation",
            "EXAMPLE",
            r"tools\a.py",
        )
        b = make_resource_key(
            "IMPLEMENTATION",
            "example",
            "tools/a.py",
        )

        self.assertEqual(
            make_resource_id(a),
            make_resource_id(b),
        )

    def test_missing_kind_fails_closed(self):
        with self.assertRaises(ValueError):
            make_resource_key(
                "",
                "EXAMPLE",
                "a.py",
            )

    def test_missing_identity_fails_closed(self):
        with self.assertRaises(ValueError):
            make_resource_key(
                "IMPLEMENTATION",
                "",
                "a.py",
            )

    def test_missing_path_fails_closed(self):
        with self.assertRaises(ValueError):
            make_resource_key(
                "IMPLEMENTATION",
                "EXAMPLE",
                "",
            )

    def test_allocation_is_deterministic(self):
        values = [
            {
                "kind": "IMPLEMENTATION",
                "canonical_identity": "B",
                "path": "b.py",
            },
            {
                "kind": "IMPLEMENTATION",
                "canonical_identity": "A",
                "path": "a.py",
            },
        ]

        self.assertEqual(
            allocate_resource_ids(values),
            allocate_resource_ids(list(reversed(values))),
        )


if __name__ == "__main__":
    unittest.main()
