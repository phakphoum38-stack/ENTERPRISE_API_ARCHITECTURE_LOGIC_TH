from __future__ import annotations

import json
import unittest
from pathlib import Path

from owner_special.research_os_friend import aeos_assurance_check_fabric as fabric


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "current" / "AEOS_ASSURANCE_CHECK_REGISTRY.json"


class AEOSAssuranceCheckFabricTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

    def test_registry_is_fail_closed_and_unique(self) -> None:
        summary = fabric.validate_registry()
        self.assertEqual(summary["baseline_sha"], "c04d60b36d51eb8529a4c65a61c7d5a411e5fe85")
        ids = [item["id"] for item in self.registry["checks"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(ids), 80)

    def test_pass_requires_independent_fresh_evidence(self) -> None:
        report = {
            "baseline_sha": self.registry["baseline_sha"],
            "observed_sha": self.registry["baseline_sha"],
            "checks": {
                item["id"]: {
                    "status": "PASS",
                    "evidence_refs": [f"EV-{index:03d}"],
                    "independent": True,
                    "fresh": True,
                }
                for index, item in enumerate(self.registry["checks"], start=1)
            },
        }
        result = fabric.validate_report(report, self.registry, self.registry["baseline_sha"])
        self.assertEqual(result["report_status"], "PASS")

    def test_unknown_cannot_pass(self) -> None:
        report = {
            "baseline_sha": self.registry["baseline_sha"],
            "observed_sha": self.registry["baseline_sha"],
            "checks": {
                item["id"]: {
                    "status": "PASS",
                    "evidence_refs": ["EV"],
                    "independent": True,
                    "fresh": True,
                }
                for item in self.registry["checks"]
            },
        }
        report["checks"][self.registry["checks"][0]["id"]]["status"] = "UNKNOWN"
        with self.assertRaises(fabric.AssuranceCheckError):
            fabric.validate_report(report, self.registry, self.registry["baseline_sha"])

    def test_self_attested_pass_is_rejected(self) -> None:
        report = {
            "baseline_sha": self.registry["baseline_sha"],
            "observed_sha": self.registry["baseline_sha"],
            "checks": {
                item["id"]: {
                    "status": "PASS",
                    "evidence_refs": ["EV"],
                    "independent": True,
                    "fresh": True,
                }
                for item in self.registry["checks"]
            },
        }
        report["checks"][self.registry["checks"][0]["id"]]["self_attested"] = True
        with self.assertRaises(fabric.AssuranceCheckError):
            fabric.validate_report(report, self.registry, self.registry["baseline_sha"])

    def test_exact_head_fence_rejects_wrong_sha(self) -> None:
        report = {
            "baseline_sha": self.registry["baseline_sha"],
            "observed_sha": "0" * 40,
            "checks": {},
        }
        with self.assertRaises(fabric.AssuranceCheckError):
            fabric.validate_report(report, self.registry, self.registry["baseline_sha"])


if __name__ == "__main__":
    unittest.main()
