import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from analyze_workflow_failure import classify, protected_hit
from certify_release_spine import main as certify_main
from generate_workflow_repair import SAFE_RULES
from validate_failure_memory import main as memory_main


class WorkflowIntelligenceTests(unittest.TestCase):
    def test_target_sha_mismatch_is_protected(self):
        code, action = classify("SOURCE_SHA_MISMATCH: target=abc checkout=def")
        self.assertEqual(code, "TARGET_SHA_MISMATCH")
        self.assertEqual(action, "protected_stop")

    def test_provenance_failure_is_protected(self):
        code, action = classify("installed commit mismatch and installed sha256 mismatch")
        self.assertEqual(code, "PROVENANCE_FAILURE")
        self.assertEqual(action, "protected_stop")

    def test_identity_failure_is_protected(self):
        code, action = classify("OWNER BUILD IDENTITY gate failed")
        self.assertEqual(code, "IDENTITY_FAILURE")
        self.assertEqual(action, "protected_stop")

    def test_artifact_failure_is_not_silently_trusted(self):
        code, action = classify("download-artifact failed: artifact not found")
        self.assertEqual(code, "ARTIFACT_FAILURE")
        self.assertEqual(action, "investigate_artifact_lineage")

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

    def test_certification_rejects_self_asserted_certification(self):
        sha = "a" * 40
        evidence = {
            "version": 1,
            "immutable": True,
            "workflow": "test",
            "run_id": "123",
            "commit": sha,
            "evidence": [],
            "gates": {stage: True for stage in ["SOURCE", "QUALITY", "BUILD", "IDENTITY", "PACKAGE", "INSTALL_E2E", "PROVENANCE", "LINEAGE", "CANDIDATE", "CERTIFICATION", "RELEASE"]},
            "protected_gates": {name: True for name in ["TARGET_SHA", "OWNER_BUILD_IDENTITY", "SHA256", "INSTALLED_PROVENANCE", "CANONICAL_LINEAGE"]},
        }
        evidence["manifest_sha256"] = hashlib.sha256(json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_path = root / "evidence.json"
            output_path = root / "certification.json"
            contract = root / "contract.yml"
            contract.write_text("release_spine:\n" + "".join(f"  - {s}\n" for s in ["SOURCE", "QUALITY", "BUILD", "IDENTITY", "PACKAGE", "INSTALL_E2E", "PROVENANCE", "LINEAGE", "CANDIDATE", "CERTIFICATION", "RELEASE"]), encoding="utf-8")
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            argv = ["certify_release_spine.py", "--contract", str(contract), "--evidence", str(evidence_path), "--target-sha", sha, "--output", str(output_path)]
            with patch("sys.argv", argv):
                self.assertNotEqual(certify_main(), 0)
            result = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "FAIL")
            self.assertTrue(any("self-assert" in e for e in result["errors"]))

    def test_failure_memory_seed_is_verified_only(self):
        with tempfile.TemporaryDirectory() as td:
            memory = Path(td) / "memory.json"
            output = Path(td) / "memory-validation.json"
            memory.write_text(json.dumps({"version": 1, "policy": {"only_verified": True}, "entries": []}), encoding="utf-8")
            argv = ["validate_failure_memory.py", "--memory", str(memory), "--output", str(output)]
            with patch("sys.argv", argv):
                self.assertEqual(memory_main(), 0)


if __name__ == "__main__":
    unittest.main()
