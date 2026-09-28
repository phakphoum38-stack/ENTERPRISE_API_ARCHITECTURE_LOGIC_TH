import unittest

from tools.research_os_m2_platform import M2Platform


class M2PlatformTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m2 = M2Platform()

    def test_source_is_pinned(self):
        self.assertRegex(self.m2.source_sha, r"^[0-9a-f]{40}$")

    def test_search_finds_runner(self):
        results = self.m2.search("runner")
        self.assertTrue(results)

    def test_vertical_search_traverses_relationships(self):
        result = self.m2.vertical("runner", depth=8)
        self.assertTrue(result["roots"])
        self.assertTrue(result["nodes"])

    def test_horizontal_search_returns_relationships(self):
        result = self.m2.horizontal("runner")
        self.assertTrue(result["roots"])
        self.assertIn("relations", result)

    def test_impact_is_explicit(self):
        result = self.m2.impact("runner")
        self.assertIn("contracts", result["impact"])
        self.assertIn("final_gate", result["impact"])

    def test_platform_graph_is_reused_and_validated(self):
        result = self.m2.platform_graph_summary()
        self.assertEqual(result["validation_failures"], [])

    def test_resume_is_source_based(self):
        result = self.m2.resume()
        self.assertTrue(result["chat_is_not_source_of_truth"])
        self.assertRegex(result["source_sha"], r"^[0-9a-f]{40}$")


if __name__ == "__main__":
    unittest.main()
