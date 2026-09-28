import unittest

from owner_special.research_os_friend import ToolSearch, ToolState, UnifiedToolCatalog


class ToolSearchTests(unittest.TestCase):
    def setUp(self):
        self.search = ToolSearch()

    def test_exact_tool_name_ranks_first(self):
        results = self.search.search("github")
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0].name, "github")
        self.assertGreater(results[0].score, results[1].score if len(results) > 1 else 0)

    def test_query_is_deterministic_and_bounded(self):
        first = self.search.search("validation", limit=2)
        second = self.search.search("validation", limit=2)
        self.assertEqual(first, second)
        self.assertLessEqual(len(first), 2)

    def test_filters_do_not_change_catalog(self):
        catalog = UnifiedToolCatalog()
        before = catalog.all()
        results = self.search.search("github", states=(ToolState.EXTERNAL,))
        self.assertTrue(all(item.state == ToolState.EXTERNAL.value for item in results))
        self.assertEqual(catalog.all(), before)

    def test_empty_query_returns_bounded_catalog_without_execution(self):
        results = self.search.search("", limit=3)
        self.assertEqual(tuple(item.name for item in results), ("echo", "file", "git-branch"))

    def test_invalid_limit_fails_fast(self):
        with self.assertRaises(ValueError):
            self.search.search("github", limit=0)


if __name__ == "__main__":
    unittest.main()
