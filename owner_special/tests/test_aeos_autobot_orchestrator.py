import unittest

from tools.aeos_autobot_evidence_manifest import evidence_id
from tools.aeos_autobot_orchestrator import Job, run_wave
from tools.aeos_autobot_state_machine import Evidence, ResultState, Snapshot


class TestAutobotOrchestrator(unittest.TestCase):
    def snapshot(self, set_id, source_sha="a" * 40, iteration="iteration-1"):
        return Snapshot(iteration, source_sha, set_id, "W0", "noop", ".")

    def job(self, set_id, state, source_sha="a" * 40, iteration="iteration-1"):
        snap = self.snapshot(set_id, source_sha, iteration)
        return Job(snap, lambda actual: Evidence(actual, state, evidence_id(actual, state)))

    def test_parallel_all_pass_waits_for_all(self):
        result = run_wave("W0", [self.job("S01", ResultState.PASSED), self.job("S02", ResultState.PASSED)])
        self.assertEqual(result.decision, ResultState.PASSED)
        self.assertEqual(len(result.evidence), 2)

    def test_failure_blocks_wave(self):
        result = run_wave("W0", [self.job("S01", ResultState.PASSED), self.job("S02", ResultState.FAILED)])
        self.assertEqual(result.decision, ResultState.HOLD)

    def test_worker_exception_is_infra_failure(self):
        snap = self.snapshot("S01")
        result = run_wave("W0", [Job(snap, lambda _: (_ for _ in ()).throw(RuntimeError("boom")))])
        self.assertEqual(result.decision, ResultState.HOLD)
        self.assertEqual(result.evidence[0].result_state, ResultState.INFRA_FAILED)

    def test_snapshot_source_mismatch_is_rejected(self):
        with self.assertRaises(ValueError):
            run_wave("W0", [self.job("S01", ResultState.PASSED), self.job("S02", ResultState.PASSED, source_sha="b" * 40)])

    def test_snapshot_iteration_mismatch_is_rejected(self):
        with self.assertRaises(ValueError):
            run_wave("W0", [self.job("S01", ResultState.PASSED), self.job("S02", ResultState.PASSED, iteration="iteration-old")])

    def test_duplicate_set_is_rejected(self):
        with self.assertRaises(ValueError):
            run_wave("W0", [self.job("S01", ResultState.PASSED), self.job("S01", ResultState.PASSED)])

    def test_empty_wave_is_hold(self):
        result = run_wave("W0", [])
        self.assertEqual(result.decision, ResultState.HOLD)


if __name__ == "__main__":
    unittest.main()
