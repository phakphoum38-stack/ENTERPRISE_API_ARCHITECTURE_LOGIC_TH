from __future__ import annotations

import unittest

from v3.research_os_v3.runtime_failure_evidence import RuntimeFailureEvidenceBuilder


class RuntimeFailureEvidenceTests(unittest.TestCase):
    TARGET = "850b772d715d3f4854681b263d9fa6f8e1100fa3"

    def test_evidence_hash_is_deterministic(self):
        builder = RuntimeFailureEvidenceBuilder(self.TARGET)
        observations = {
            "reclaimed": True,
            "stale_owner_rejected": True,
            "final_status": "completed",
        }
        first = builder.build("worker_crash_before_ack", observations)
        second = builder.build("worker_crash_before_ack", observations)
        self.assertEqual(first.evidence_hash, second.evidence_hash)
        self.assertEqual(self.TARGET, first.target_sha)

    def test_target_identity_is_required(self):
        with self.assertRaises(ValueError):
            RuntimeFailureEvidenceBuilder("not-a-sha")

    def test_evidence_is_bound_to_scenario_and_target(self):
        builder = RuntimeFailureEvidenceBuilder(self.TARGET)
        first = builder.build("worker_crash_before_ack", {"reclaimed": True})
        second = builder.build("event_crash_before_ack", {"reclaimed": True})
        self.assertNotEqual(first.evidence_hash, second.evidence_hash)
        self.assertEqual(self.TARGET, second.target_sha)


if __name__ == "__main__":
    unittest.main()
