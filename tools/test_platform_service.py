import unittest

from tools.platform_service import PlatformService


class PlatformServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = PlatformService()

    def test_recon_is_source_pinned_and_read_only(self):
        result = self.service.recon()
        self.assertRegex(result["source_sha"], r"^[0-9a-f]{40}$")
        self.assertEqual(result["platform_graph_failures"], [])
        self.assertEqual(result["project_registry_failures"], [])

    def test_search_and_vertical(self):
        self.assertTrue(self.service.search("runner")["results"])
        self.assertTrue(self.service.vertical("runner", depth=8)["nodes"])

    def test_horizontal_and_impact(self):
        self.assertIn("relations", self.service.horizontal("runner"))
        impact = self.service.impact("runner")
        self.assertIn("contracts", impact["impact"])

    def test_projects_use_shared_boundaries(self):
        result = self.service.project_validate()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["project_count"], 1)

    def test_snapshot_contains_required_continuity_state(self):
        snapshot = self.service.snapshot()
        for field in (
            "source_sha", "active_work", "deferred_work", "decisions",
            "verified_truths", "evidence_refs", "authority_boundaries",
        ):
            self.assertIn(field, snapshot)

    def test_resume_holds_on_sha_mismatch(self):
        snapshot = self.service.snapshot()
        snapshot["source_sha"] = "0" * 40
        result = self.service.resume(snapshot)
        self.assertEqual(result["status"], "HOLD")
        self.assertIn("source_sha_mismatch", result["failures"])


if __name__ == "__main__":
    unittest.main()
