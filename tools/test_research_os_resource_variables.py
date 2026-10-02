import unittest

from tools.research_os_resource_variables import (
    RESOURCE_VARIABLE_SCHEMA,
    create_variable,
    validate_variables,
    variables_from_mapping,
)


class ResourceVariableTests(unittest.TestCase):

    def test_create_variable(self):
        value = create_variable(
            "API_PORT",
            "integer",
            8787,
        )
        self.assertEqual(value.type, "INTEGER")
        self.assertEqual(value.value, 8787)

    def test_required_missing_fails_closed(self):
        with self.assertRaises(ValueError):
            create_variable(
                "API_PORT",
                "INTEGER",
                required=True,
            )

    def test_invalid_type_fails_closed(self):
        with self.assertRaises(ValueError):
            create_variable(
                "X",
                "INVALID",
            )

    def test_duplicate_names_fail_closed(self):
        values = [
            create_variable("X", "STRING", "a"),
            create_variable("X", "STRING", "b"),
        ]

        with self.assertRaises(ValueError):
            validate_variables(values)

    def test_mapping_is_deterministic(self):
        values = {
            "Z": {"type": "STRING", "value": "z"},
            "A": {"type": "PATH", "value": "a"},
        }

        a = variables_from_mapping(values)
        b = variables_from_mapping(
            dict(reversed(list(values.items())))
        )

        self.assertEqual(a, b)
        self.assertEqual(
            [x.name for x in a],
            ["A", "Z"],
        )

    def test_schema_exists(self):
        self.assertTrue(
            RESOURCE_VARIABLE_SCHEMA.endswith("_V1")
        )


if __name__ == "__main__":
    unittest.main()
