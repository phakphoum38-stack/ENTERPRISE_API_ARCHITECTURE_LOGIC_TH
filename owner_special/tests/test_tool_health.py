import unittest

from research_os_friend.runtime import FriendRuntime


class ToolHealthTests(unittest.TestCase):
    def test_runtime_health_reports_canonical_ready_tools(self) -> None:
        runtime = FriendRuntime.create_owner_special("owner-test")
        health = runtime.tool_health()

        self.assertEqual(health["total"], 15)
        self.assertEqual(health["healthy"], 7)
        self.assertEqual(health["counts"]["ready"], 7)
        self.assertEqual(health["counts"]["implemented_unregistered"], 5)
        self.assertEqual(health["counts"]["needs_connection"], 1)
        self.assertEqual(health["counts"]["external"], 2)

    def test_health_rows_match_catalog(self) -> None:
        runtime = FriendRuntime.create_owner_special("owner-test")
        health = runtime.tool_health()
        catalog = runtime.tool_catalog()

        self.assertEqual(health["rows"], catalog)
        self.assertEqual({row["name"] for row in health["rows"]}, {row["name"] for row in catalog})


if __name__ == "__main__":
    unittest.main()
