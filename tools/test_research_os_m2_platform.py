import os
import tempfile
import unittest
from unittest.mock import patch

from tools.research_os_m2_platform import M2Platform
from tools.platform_work_checkpoint import create_checkpoint


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

    def test_resume_checkpoint_is_consumed(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"RESEARCH_OS_DATA_DIR": tmp}, clear=False):
                sha = self.m2.source_sha
                with patch(
                    "tools.platform_work_checkpoint.canonical_sha",
                    return_value=sha,
                ):
                    create_checkpoint(
                        owner_id="owner",
                        task_id="m2-resume-test",
                        workflow_state="ACTIVE",
                        current_step="recon",
                        pending_steps=["inspect"],
                        evidence_refs=["evidence:m2"],
                        deferred_work=["deferred:m2"],
                        source_sha=sha,
                    )

                    result = self.m2.resume()

        self.assertEqual(result["checkpoint_status"], "READY")
        self.assertIn("m2-resume-test", result["active_work"])
        self.assertIn("deferred:m2", result["deferred_work"])
        self.assertIn("evidence:m2", result["evidence"])
        self.assertEqual(result["resume_failures"], [])
        self.assertEqual(result["decisions"], [])

    def test_resume_checkpoint_sha_drift_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"RESEARCH_OS_DATA_DIR": tmp}, clear=False):
                original_sha = self.m2.source_sha
                drifted_sha = "0" * 40

                with patch(
                    "tools.platform_work_checkpoint.canonical_sha",
                    return_value=original_sha,
                ):
                    create_checkpoint(
                        owner_id="owner",
                        task_id="m2-sha-drift-test",
                        workflow_state="ACTIVE",
                        current_step="recon",
                        source_sha=original_sha,
                    )

                with patch(
                    "tools.platform_work_checkpoint.canonical_sha",
                    return_value=drifted_sha,
                ):
                    result = self.m2.resume()

        self.assertEqual(result["checkpoint_status"], "HOLD")
        self.assertTrue(
            any(
                failure.startswith("source_sha_mismatch:")
                for failure in result["resume_failures"]
            )
        )
        self.assertEqual(
            result["next_step"],
            "HOLD: reconcile checkpoint source SHA before mutation.",
        )


if __name__ == "__main__":
    unittest.main()
