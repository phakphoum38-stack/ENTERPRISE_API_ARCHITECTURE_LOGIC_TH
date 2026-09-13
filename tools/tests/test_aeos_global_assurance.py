import unittest

from tools.aeos_failure_algebra import FailureObservation, classify, digest, is_non_passing_state
from tools.aeos_novelty_firewall import evaluate_novelty


TAXONOMY = {
    "failure_taxonomy": {
        "authority": ["AUTHORITY_VIOLATION"],
        "execution": ["CHECKOUT_SHA_MISMATCH"],
    }
}


class GlobalAssuranceTests(unittest.TestCase):
    def make_observation(self, **overrides):
        values = {
            "actor": "agent",
            "object": "authority proof",
            "boundary": "policy",
            "state": "invalid",
            "time": "current",
            "evidence": "missing",
            "authority": "AUTHORITY_VIOLATION",
            "dependency": "none",
            "environment": "ci",
            "action": "certify",
            "consequence": "blocked",
        }
        values.update(overrides)
        return FailureObservation(**values)

    def test_fingerprint_is_deterministic(self):
        left = self.make_observation()
        right = self.make_observation()
        self.assertEqual(left.fingerprint, right.fingerprint)
        self.assertEqual(digest(left.canonical()), digest(right.canonical()))

    def test_taxonomy_classification_is_explicit(self):
        self.assertEqual(classify(self.make_observation(), TAXONOMY), "AUTHORITY_VIOLATION")

    def test_unknown_is_not_passing(self):
        self.assertTrue(is_non_passing_state("UNKNOWN"))
        decision = evaluate_novelty("UNKNOWN")
        self.assertFalse(decision.allowed_to_certify)

    def test_unclassified_is_not_passing(self):
        decision = evaluate_novelty("some-new-condition")
        self.assertFalse(decision.allowed_to_certify)
        self.assertEqual(decision.classification, "UNCLASSIFIED")

    def test_verified_requires_independent_proof(self):
        self.assertFalse(evaluate_novelty("VERIFIED").allowed_to_certify)
        self.assertTrue(evaluate_novelty("VERIFIED", independently_verified=True).allowed_to_certify)

    def test_stale_and_conflict_are_blocked(self):
        for state in ("STALE", "CONFLICT", "NOT_OBSERVED", "QUARANTINED"):
            self.assertFalse(evaluate_novelty(state).allowed_to_certify)


if __name__ == "__main__":
    unittest.main()
