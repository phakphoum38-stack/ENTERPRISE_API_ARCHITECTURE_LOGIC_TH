import unittest

from tools.research_os_resource_parser import (
    declared_identities,
    explicit_identities,
)


class ResourceParserTests(unittest.TestCase):

    def test_python_type_annotation_is_not_identity(self):
        values = declared_identities(
            "tools/example.py",
            "resource_id: str\ncontract_id: str\n",
        )

        self.assertNotIn("str", values)
        self.assertIn("example", values)

    def test_yaml_identity_is_discovered(self):
        values = declared_identities(
            "current/example.yml",
            "contract_id: REAL_CONTRACT\n",
        )

        self.assertIn("real_contract", values)

    def test_json_identity_is_discovered(self):
        values = explicit_identities(
            "current/example.json",
            '{"contract":"REAL_CONTRACT"}',
        )

        self.assertIn("real_contract", values)

    def test_path_stem_is_not_explicit_identity(self):
        values = explicit_identities(
            "foo_contract.json",
            '{"contract":"REAL_CONTRACT"}',
        )

        self.assertNotIn("foo_contract", values)
        self.assertIn("real_contract", values)


if __name__ == "__main__":
    unittest.main()
