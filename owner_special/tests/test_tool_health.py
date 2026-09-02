import unittest

from research_os_friend.runtime import FriendRuntime


class ToolHealthTests(unittest.TestCase):
    def test_runtime_health_reports_registered_v3_tools_as_ready(self) -> None:
        runtime = FriendRuntime.create_owner_special("owner-test")
        health = runtime.tool_health()

        self.assertEqual(health["total"], 19)
        self.assertEqual(health["healthy"], 17)
        self.assertEqual(health["counts"]["ready"], 17)
        self.assertEqual(health["counts"]["needs_connection"], 2)

    def test_health_rows_match_catalog(self) -> None:
        runtime = FriendRuntime.create_owner_special("owner-test")
        health = runtime.tool_health()
        catalog = runtime.tool_catalog()

        self.assertEqual(health["rows"], catalog)
        self.assertEqual({row["name"] for row in health["rows"]}, {row["name"] for row in catalog})


if __name__ == "__main__":
    unittest.main()
