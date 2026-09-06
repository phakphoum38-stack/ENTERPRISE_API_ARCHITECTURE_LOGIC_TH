import unittest

from owner_special.research_os_friend import McpDiscoveryBoundary, McpToolDescriptor


class McpBoundaryTests(unittest.TestCase):
    def test_discovery_is_deterministic_and_bounded(self):
        descriptors = (
            McpToolDescriptor("shell.run", "run shell", "local", side_effect=True),
            McpToolDescriptor("search", "search docs", "docs", capability="docs.search"),
            McpToolDescriptor("fetch", "fetch page", "web", capability="web.fetch"),
        )
        boundary = McpDiscoveryBoundary()
        first = boundary.discover(descriptors, limit=2)
        second = boundary.discover(descriptors, limit=2)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 2)

    def test_side_effect_descriptor_requires_approval(self):
        result = McpDiscoveryBoundary().discover(
            (McpToolDescriptor("shell.run", "run", "local", side_effect=True),)
        )
        self.assertTrue(result[0].approval_required)

    def test_query_filters_without_execution(self):
        result = McpDiscoveryBoundary().discover(
            (McpToolDescriptor("search", "search docs", "docs"),),
            query="docs",
        )
        self.assertEqual(result[0].name, "search")

    def test_remote_execution_is_disabled_in_boundary_phase(self):
        status = McpDiscoveryBoundary().execution_status()
        self.assertFalse(status["remote_execution"])
        self.assertFalse(status["approval_bypass"])


if __name__ == "__main__":
    unittest.main()
