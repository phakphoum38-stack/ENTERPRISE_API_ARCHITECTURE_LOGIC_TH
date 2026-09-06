import json
import tempfile
import unittest
from pathlib import Path

from analyze_workflow_failure import classify, protected_hit
from generate_workflow_repair import SAFE_RULES


class WorkflowIntelligenceTests(unittest.TestCase):
    def test_target_sha_mismatch_is_protected(self):
        code, action = classify("SOURCE_SHA_MISMATCH: target=abc checkout=def")
        self.assertEqual(code, "TARGET_SHA_MISMATCH")
        self.assertEqual(action, "protected_stop")

    def test_provenance_mentions_are_detected(self):
        hits = protected_hit("RELEASE_PROVENANCE_GATE=FAIL TARGET_SHA SHA256")
        self.assertIn("TARGET_SHA", hits)
        self.assertIn("SHA256", hits)
        self.assertIn("INSTALLED_PROVENANCE", protected_hit("installed provenance failed"))

    def test_known_safe_rules_are_bounded(self):
        self.assertIn("STALE_LASTEXITCODE", SAFE_RULES)
        self.assertIn("TRANSIENT_NETWORK", SAFE_RULES)
        self.assertIn("YAML_FAILURE", SAFE_RULES)

    def test_unknown_failure_is_not_auto_repaired(self):
        code, action = classify("some completely new failure")
        self.assertEqual(code, "UNKNOWN_FAILURE")
        self.assertEqual(action, "human_review")


if __name__ == "__main__":
    unittest.main()
