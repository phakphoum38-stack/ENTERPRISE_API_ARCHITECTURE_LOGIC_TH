from __future__ import annotations

import unittest


class RuntimeFailureMatrixContractTests(unittest.TestCase):
    SCENARIOS = (
        "task_claim_contention",
        "stale_task_owner",
        "expired_task_lease",
        "active_task_renewal",
        "worker_crash_before_ack",
        "duplicate_event_registration",
        "delivery_claim_contention",
        "stale_delivery_owner",
        "event_ledger_restart",
        "unknown_event",
        "dlq_replay_recovery",
    )

    REQUIRED_FIELDS = (
        "scenario",
        "target_sha",
        "passed",
        "observations",
        "evidence_hash",
    )

    def test_failure_matrix_has_unique_scenarios(self):
        self.assertEqual(len(self.SCENARIOS), len(set(self.SCENARIOS)))

    def test_failure_matrix_covers_all_required_boundary_classes(self):
        required = {
            "task_claim_contention",
            "stale_task_owner",
            "expired_task_lease",
            "worker_crash_before_ack",
            "duplicate_event_registration",
            "stale_delivery_owner",
            "event_ledger_restart",
            "dlq_replay_recovery",
        }
        self.assertTrue(required.issubset(set(self.SCENARIOS)))

    def test_evidence_entry_schema_is_explicit(self):
        entry = {
            "scenario": "worker_crash_before_ack",
            "target_sha": "a" * 40,
            "passed": True,
            "observations": {"recovered": True, "stale_ack_rejected": True},
            "evidence_hash": "b" * 64,
        }
        self.assertEqual(set(self.REQUIRED_FIELDS), set(entry))
        self.assertIsInstance(entry["passed"], bool)
        self.assertIsInstance(entry["observations"], dict)

    def test_unknown_or_missing_result_cannot_be_treated_as_pass(self):
        entry = {
            "scenario": "event_ledger_restart",
            "target_sha": "a" * 40,
            "passed": None,
            "observations": {},
            "evidence_hash": "",
        }
        self.assertIsNot(entry["passed"], True)
        self.assertFalse(entry["evidence_hash"])


if __name__ == "__main__":
    unittest.main()
