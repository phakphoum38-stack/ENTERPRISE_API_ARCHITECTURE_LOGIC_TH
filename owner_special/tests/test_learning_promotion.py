import unittest

from owner_special.research_os_friend.learning_promotion import (
    LearningCandidate,
    LearningPromotionError,
    evaluate_promotion,
    snapshot_candidate,
)


class LearningPromotionTests(unittest.TestCase):
    def setUp(self):
        self.kwargs = dict(
            owner="owner_special",
            source_sha="1" * 40,
            correlation_id="h10-test",
            name="repair dependency",
            goal="record a verified dependency repair",
            procedure=("inspect failure", "apply minimal repair", "verify CI"),
            evidence_fingerprint="a" * 64,
            confidence=0.95,
        )

    def test_verified_candidate_can_be_promoted(self):
        candidate = LearningCandidate(**self.kwargs)
        self.assertTrue(evaluate_promotion(candidate, evidence_verified=True))

    def test_unverified_candidate_is_not_promoted(self):
        candidate = LearningCandidate(**self.kwargs)
        self.assertFalse(evaluate_promotion(candidate, evidence_verified=False))

    def test_low_confidence_candidate_is_not_promoted(self):
        candidate = LearningCandidate(**{**self.kwargs, "confidence": 0.79})
        self.assertFalse(evaluate_promotion(candidate, evidence_verified=True))

    def test_core_skill_is_rejected(self):
        with self.assertRaises(LearningPromotionError):
            LearningCandidate(**{**self.kwargs, "core_skill": True})

    def test_secret_like_content_is_rejected(self):
        with self.assertRaises(LearningPromotionError):
            LearningCandidate(**{**self.kwargs, "goal": "store api_key"})

    def test_snapshot_is_detached(self):
        candidate = LearningCandidate(**self.kwargs)
        snapshot = snapshot_candidate(candidate)
        snapshot["procedure"].append("mutate copy")
        self.assertEqual(len(candidate.procedure), 3)

    def test_fingerprint_is_deterministic(self):
        first = LearningCandidate(**self.kwargs)
        second = LearningCandidate(**self.kwargs)
        self.assertEqual(first.fingerprint, second.fingerprint)


if __name__ == "__main__":
    unittest.main()
