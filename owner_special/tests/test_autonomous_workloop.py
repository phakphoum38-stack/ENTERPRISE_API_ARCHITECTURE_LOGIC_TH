import unittest

from owner_special.research_os_friend.autonomous_workloop import (
    WorkItem,
    WorkState,
    WorkloopError,
    build_stop_proof,
    can_stop,
)


SHA = "c04d60b36d51eb8529a4c65a61c7d5a411e5fe85"


class AutonomousWorkloopTests(unittest.TestCase):
    def test_normal_lifecycle_requires_each_gate_in_order(self):
        item = WorkItem("M1", "W1", "build feature", SHA)
        item = item.transition(WorkState.CONTRACTED)
        item = item.transition(WorkState.PLANNED)
        item = item.transition(WorkState.QUEUED)
        item = item.transition(WorkState.LEASED, lease_id="L1")
        item = item.transition(WorkState.BRANCHED, observed_sha=SHA)
        item = item.transition(WorkState.DOCUMENTED, observed_sha=SHA)
        item = item.transition(WorkState.IMPLEMENTED, observed_sha=SHA)
        item = item.transition(WorkState.DIFF_CAPTURED, observed_sha=SHA)
        self.assertEqual(item.state, WorkState.DIFF_CAPTURED)

    def test_skipping_gate_is_rejected(self):
        item = WorkItem("M1", "W1", "build feature", SHA)
        with self.assertRaises(WorkloopError):
            item.transition(WorkState.PLANNED)

    def test_stale_sha_is_rejected(self):
        item = WorkItem("M1", "W1", "build feature", SHA)
        with self.assertRaises(WorkloopError):
            item.transition(WorkState.BRANCHED, observed_sha="0" * 40, lease_id="L1")

    def test_mutation_adjacent_state_requires_lease(self):
        item = WorkItem("M1", "W1", "build feature", SHA)
        item = item.transition(WorkState.CONTRACTED)
        item = item.transition(WorkState.PLANNED)
        item = item.transition(WorkState.QUEUED)
        item = item.transition(WorkState.LEASED, lease_id="L1")
        with self.assertRaises(WorkloopError):
            item.transition(WorkState.BRANCHED)

    def test_mutation_adjacent_state_requires_exact_lease(self):
        item = WorkItem("M1", "W1", "build feature", SHA)
        item = item.transition(WorkState.CONTRACTED)
        item = item.transition(WorkState.PLANNED)
        item = item.transition(WorkState.QUEUED)
        item = item.transition(WorkState.LEASED, lease_id="L1")
        with self.assertRaises(WorkloopError):
            item.transition(WorkState.BRANCHED, observed_sha=SHA, lease_id="L2")

    def test_failure_requires_evidence_and_quarantines(self):
        item = WorkItem("M1", "W1", "build feature", SHA)
        failed = item.failure("CI_FAILURE", ("EV-1",))
        self.assertEqual(failed.state, WorkState.QUARANTINED)
        self.assertTrue(failed.failure_fingerprint)
        self.assertEqual(failed.attempt_count, 1)

    def test_stop_requires_zero_all_blockers(self):
        self.assertTrue(can_stop(required_work=0, recovery_work=0, unresolved_failures=0, unknown=0,
                                 stale=0, unverified=0, blocked_required=0,
                                 uncertified_integrations=0, main_verified=True, final_rescan=True))
        self.assertFalse(can_stop(required_work=1, recovery_work=0, unresolved_failures=0, unknown=0,
                                  stale=0, unverified=0, blocked_required=0,
                                  uncertified_integrations=0, main_verified=True, final_rescan=True))

    def test_stop_proof_is_hold_when_observation_is_missing(self):
        proof = build_stop_proof()
        self.assertEqual(proof["status"], "HOLD")
        self.assertEqual(proof["terminal_state"], "ACTIVE")

    def test_stop_proof_rejects_string_boolean_coercion(self):
        with self.assertRaises(WorkloopError):
            build_stop_proof(required_work=0, recovery_work=0, unresolved_failures=0,
                             unknown=0, stale=0, unverified=0, blocked_required=0,
                             uncertified_integrations=0, main_verified="false", final_rescan=True)

    def test_stop_proof_rejects_negative_counts(self):
        with self.assertRaises(WorkloopError):
            build_stop_proof(required_work=-1, recovery_work=0, unresolved_failures=0,
                             unknown=0, stale=0, unverified=0, blocked_required=0,
                             uncertified_integrations=0, main_verified=True, final_rescan=True)

    def test_stop_proof_is_certified_idle_only_after_final_rescan(self):
        proof = build_stop_proof(required_work=0, recovery_work=0, unresolved_failures=0,
                                 unknown=0, stale=0, unverified=0, blocked_required=0,
                                 uncertified_integrations=0, main_verified=True, final_rescan=True)
        self.assertEqual(proof["status"], "PASS")
        self.assertEqual(proof["terminal_state"], "CERTIFIED_IDLE")

    def test_terminal_state_cannot_continue(self):
        item = WorkItem("M1", "W1", "build feature", SHA)
        item = WorkItem(**{**item.__dict__, "state": WorkState.COMPLETED})
        with self.assertRaises(WorkloopError):
            item.transition(WorkState.MISSION_CREATED)


if __name__ == "__main__":
    unittest.main()
