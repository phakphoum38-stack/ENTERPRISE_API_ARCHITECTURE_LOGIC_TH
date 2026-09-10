import unittest

from tools.aeos_autobot_state_machine import (
    Barrier,
    Evidence,
    ResultState,
    Snapshot,
    State,
    all_passed,
    bounded_recovery_attempt,
    reject_stale,
)


class TestAutobotStateMachine(unittest.TestCase):
    def snapshot(self, iteration="i-1", wave="W0", set_id="S01"):
        return Snapshot(
            iteration_id=iteration,
            source_sha="a" * 40,
            set_id=set_id,
            wave_id=wave,
            command="python -m unittest",
            cwd=".",
        )

    def evidence(self, state, iteration="i-1", wave="W0", set_id="S01"):
        return Evidence(self.snapshot(iteration, wave, set_id), state, "e" * 64)

    def test_all_passed_requires_nonempty_complete_evidence(self):
        self.assertTrue(all_passed([self.evidence(ResultState.PASSED)]))
        self.assertFalse(all_passed([]))
        self.assertFalse(all_passed([self.evidence(ResultState.FAILED)]))

    def test_barrier_rejects_running_evidence(self):
        barrier = Barrier("W0", {"S01"})
        with self.assertRaises(ValueError):
            barrier.accept(self.evidence(ResultState.RUNNING))

    def test_barrier_rejects_wrong_wave(self):
        barrier = Barrier("W0", {"S01"})
        with self.assertRaises(ValueError):
            barrier.accept(self.evidence(ResultState.PASSED, wave="W1"))

    def test_barrier_rejects_unexpected_set(self):
        barrier = Barrier("W0", {"S01"})
        with self.assertRaises(ValueError):
            barrier.accept(self.evidence(ResultState.PASSED, set_id="S02"))

    def test_incomplete_barrier_is_hold(self):
        barrier = Barrier("W0", {"S01", "S02"})
        barrier.accept(self.evidence(ResultState.PASSED, set_id="S01"))
        self.assertFalse(barrier.complete())
        self.assertEqual(barrier.decision(), State.HOLD)

    def test_failed_barrier_is_hold(self):
        barrier = Barrier("W0", {"S01"})
        barrier.accept(self.evidence(ResultState.FAILED))
        self.assertTrue(barrier.complete())
        self.assertEqual(barrier.decision(), State.HOLD)

    def test_complete_passed_barrier_is_passed(self):
        barrier = Barrier("W0", {"S01", "S02"})
        barrier.accept(self.evidence(ResultState.PASSED, set_id="S01"))
        barrier.accept(self.evidence(ResultState.PASSED, set_id="S02"))
        self.assertTrue(barrier.complete())
        self.assertEqual(barrier.decision(), State.NEXT_WAVE)

    def test_stale_snapshot_is_rejected(self):
        active = self.snapshot(iteration="i-2")
        stale = self.evidence(ResultState.PASSED, iteration="i-1")
        with self.assertRaises(ValueError):
            reject_stale(active, stale)

    def test_cross_iteration_evidence_is_rejected(self):
        active = self.snapshot(iteration="i-2")
        old = self.evidence(ResultState.PASSED, iteration="i-1")
        with self.assertRaises(ValueError):
            reject_stale(active, old)

    def test_recovery_is_bounded(self):
        self.assertEqual(bounded_recovery_attempt(1, 3), 2)
        self.assertEqual(bounded_recovery_attempt(2, 3), 3)
        with self.assertRaises(RuntimeError):
            bounded_recovery_attempt(3, 3)


if __name__ == "__main__":
    unittest.main()
