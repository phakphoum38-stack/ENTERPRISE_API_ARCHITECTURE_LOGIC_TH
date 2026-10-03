import unittest

from tools.research_os_resource_instance import (
    RESOURCE_INSTANCE_SCHEMA,
    ResourceInstance,
    content_fingerprint,
    instance_fingerprint,
)


class ResourceInstanceTests(unittest.TestCase):

    def test_content_fingerprint_is_deterministic(self):
        first = content_fingerprint(b"research-os")
        second = content_fingerprint(b"research-os")

        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)

    def test_different_content_changes_fingerprint(self):
        first = content_fingerprint(b"a")
        second = content_fingerprint(b"b")

        self.assertNotEqual(first, second)

    def test_instance_is_deterministic(self):
        first = ResourceInstance.create(
            "RESOURCE:001",
            "tools/example.py",
            b"content",
        )
        second = ResourceInstance.create(
            "RESOURCE:001",
            "tools/example.py",
            b"content",
        )

        self.assertEqual(first, second)
        self.assertEqual(first.instance_sha256, second.instance_sha256)

    def test_path_normalization_is_deterministic(self):
        first = ResourceInstance.create(
            "RESOURCE:001",
            r"tools\example.py",
            b"content",
        )
        second = ResourceInstance.create(
            "RESOURCE:001",
            "tools/example.py",
            b"content",
        )

        self.assertEqual(first, second)

    def test_metadata_changes_instance_fingerprint(self):
        first = ResourceInstance.create(
            "RESOURCE:001",
            "tools/example.py",
            b"content",
        )
        second = ResourceInstance.create(
            "RESOURCE:002",
            "tools/example.py",
            b"content",
        )

        self.assertNotEqual(
            first.instance_sha256,
            second.instance_sha256,
        )

    def test_missing_resource_id_fails_closed(self):
        with self.assertRaises(ValueError):
            ResourceInstance.create(
                "",
                "tools/example.py",
                b"content",
            )

    def test_missing_path_fails_closed(self):
        with self.assertRaises(ValueError):
            ResourceInstance.create(
                "RESOURCE:001",
                "",
                b"content",
            )

    def test_schema_is_present(self):
        instance = ResourceInstance.create(
            "RESOURCE:001",
            "tools/example.py",
            b"content",
        )

        data = instance.to_dict()

        self.assertEqual(
            data["schema"],
            RESOURCE_INSTANCE_SCHEMA,
        )


if __name__ == "__main__":
    unittest.main()
