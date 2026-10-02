import unittest

from tools.research_os_resource_translator import (
    RESOURCE_TRANSLATOR_SCHEMA,
    translate_resource,
    translate_resources,
)


class ResourceTranslatorTests(unittest.TestCase):

    def test_translates_canonical_resource(self):
        resource = translate_resource({
            "resource_id": "abc123",
            "kind": "implementation",
            "path": r"tools\\example.py",
            "canonical_identity": "EXAMPLE",
        })

        self.assertEqual(resource.schema, RESOURCE_TRANSLATOR_SCHEMA)
        self.assertEqual(resource.kind, "IMPLEMENTATION")
        self.assertEqual(resource.path, "tools/example.py")
        self.assertEqual(resource.canonical_identity, "example")

    def test_normalizes_known_kind_alias(self):
        resource = translate_resource({
            "resource_id": "abc123",
            "kind": "source",
            "path": "tools/example.py",
            "canonical_identity": "EXAMPLE",
        })

        self.assertEqual(resource.kind, "IMPLEMENTATION")

    def test_unknown_kind_becomes_unknown(self):
        resource = translate_resource({
            "resource_id": "abc123",
            "kind": "something_new",
            "path": "example.txt",
            "canonical_identity": "EXAMPLE",
        })

        self.assertEqual(resource.kind, "UNKNOWN")

    def test_missing_resource_id_fails_closed(self):
        with self.assertRaises(ValueError):
            translate_resource({
                "kind": "implementation",
                "path": "tools/example.py",
            })

    def test_missing_path_fails_closed(self):
        with self.assertRaises(ValueError):
            translate_resource({
                "resource_id": "abc123",
                "kind": "implementation",
            })

    def test_translation_is_deterministic(self):
        resources = [
            {
                "resource_id": "b",
                "kind": "test",
                "path": "tests/b.py",
                "canonical_identity": "B",
            },
            {
                "resource_id": "a",
                "kind": "implementation",
                "path": "tools/a.py",
                "canonical_identity": "A",
            },
        ]

        first = translate_resources(resources)
        second = translate_resources(list(reversed(resources)))

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
