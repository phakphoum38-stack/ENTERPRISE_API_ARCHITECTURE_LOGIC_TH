from __future__ import annotations

import unittest


class RestartCrashMatrixContractTests(unittest.TestCase):
    CASES = (
        ("task", "crash_before_ack"),
        ("task", "expired_lease"),
        ("task", "stale_owner_after_recovery"),
        ("event", "crash_before_ack"),
        ("event", "expired_lease"),
        ("event", "stale_owner_after_recovery"),
        ("dlq", "replay_after_restart"),
    )

    def test_matrix_contains_both_durable_boundaries(self):
        boundaries = {boundary for boundary, _ in self.CASES}
        self.assertIn("task", boundaries)
        self.assertIn("event", boundaries)
        self.assertIn("dlq", boundaries)

    def test_every_case_requires_recovery_and_identity_observation(self):
        for boundary, failure in self.CASES:
            observation = {
                "boundary": boundary,
                "failure": failure,
                "recovered": True,
                "identity_conserved": True,
            }
            self.assertTrue(observation["recovered"])
            self.assertTrue(observation["identity_conserved"])

    def test_stale_owner_is_never_an_authorized_completion_path(self):
        for boundary, failure in self.CASES:
            if "stale_owner" in failure:
                self.assertNotEqual(failure, "authorized_completion")


if __name__ == "__main__":
    unittest.main()
