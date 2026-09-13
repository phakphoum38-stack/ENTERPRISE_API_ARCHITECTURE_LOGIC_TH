"""H20 promotion eligibility boundary tests."""

from __future__ import annotations

import hashlib
import json
import unittest

from owner_special.research_os_friend.learning_candidate_integrity import (
    LearningCandidateIntegrityBoundary,
    LearningCandidateIntegrityRequest,
)
from owner_special.research_os_friend.learning_candidate_version_binding import (
    LearningCandidateVersionBindingBoundary,
    LearningCandidateVersionBindingRequest,
)
from owner_special.research_os_friend.learning_promotion_eligibility import (
    LearningPromotionEligibilityBoundary,
    LearningPromotionEligibilityError,
    LearningPromotionEligibilityRequest,
)


class LearningPromotionEligibilityBoundaryTests(unittest.TestCase):
    def _integrity(self) -> dict:
        sha = "a" * 40
        skill_fp = "b" * 64
        result_fp = "c" * 64
        candidate_version = 1
        candidate = {
            "owner": "owner_special",
            "source_sha": sha,
            "correlation_id": "h20-test",
            "skill_fingerprint": skill_fp,
            "result_fingerprint": result_fp,
            "result_status": "SUCCEEDED",
        }
        bound = LearningCandidateVersionBindingBoundary().bind(
            LearningCandidateVersionBindingRequest(
                owner="owner_special",
                source_sha=sha,
                correlation_id="h20-test",
                skill_fingerprint=skill_fp,
                result_fingerprint=result_fp,
                candidate_version=candidate_version,
            ),
            {
                "schema": "research-os-learning-candidate-eligibility/v1",
                "owner": "owner_special",
                "source_sha": sha,
                "correlation_id": "h20-test",
                "skill_fingerprint": skill_fp,
                "result_fingerprint": result_fp,
                "candidate_version": candidate_version,
                "eligible": True,
                "learning_state": "LEARNED",
                "promotion_authority": "H10",
                "candidate": candidate,
                "read_only": True,
                "authority": "none",
            },
        )
        return LearningCandidateIntegrityBoundary().verify(
            LearningCandidateIntegrityRequest(
                owner="owner_special",
                source_sha=sha,
                correlation_id="h20-test",
                skill_fingerprint=skill_fp,
                result_fingerprint=result_fp,
                candidate_version=candidate_version,
                binding_fingerprint=bound["binding_fingerprint"],
            ),
            bound,
        )

    def _request(self, *, evidence_verified=True, quality_score=0.9):
        return LearningPromotionEligibilityRequest(
            owner="owner_special",
            source_sha="a" * 40,
            correlation_id="h20-test",
            skill_fingerprint="b" * 64,
            result_fingerprint="c" * 64,
            candidate_version=1,
            binding_fingerprint=self._integrity()["binding_fingerprint"],
            evidence_verified=evidence_verified,
            quality_score=quality_score,
        )

    def test_verified_high_quality_candidate_is_eligible_for_h10(self):
        snapshot = LearningPromotionEligibilityBoundary().evaluate(self._request(), self._integrity())
        self.assertEqual(snapshot["promotion_eligibility"], "ELIGIBLE_FOR_H10")
        self.assertEqual(snapshot["promotion_authority"], "H10")
        self.assertTrue(snapshot["read_only"])
        self.assertEqual(snapshot["authority"], "none")

    def test_missing_evidence_is_not_eligible(self):
        snapshot = LearningPromotionEligibilityBoundary().evaluate(self._request(evidence_verified=False), self._integrity())
        self.assertEqual(snapshot["promotion_eligibility"], "NOT_ELIGIBLE")

    def test_low_quality_is_not_eligible(self):
        snapshot = LearningPromotionEligibilityBoundary().evaluate(self._request(quality_score=0.79), self._integrity())
        self.assertEqual(snapshot["promotion_eligibility"], "NOT_ELIGIBLE")

    def test_integrity_failure_is_rejected(self):
        integrity = self._integrity()
        integrity["integrity_verified"] = False
        with self.assertRaises(LearningPromotionEligibilityError):
            LearningPromotionEligibilityBoundary().evaluate(self._request(), integrity)

    def test_identity_mismatch_is_rejected(self):
        request = self._request()
        request = LearningPromotionEligibilityRequest(**{**request.__dict__, "source_sha": "d" * 40})
        with self.assertRaises(LearningPromotionEligibilityError):
            LearningPromotionEligibilityBoundary().evaluate(request, self._integrity())

    def test_unsafe_candidate_is_rejected(self):
        integrity = self._integrity()
        integrity["candidate"]["notes"] = "javascript:alert(1)"
        with self.assertRaises(LearningPromotionEligibilityError):
            LearningPromotionEligibilityBoundary().evaluate(self._request(), integrity)

    def test_eligibility_fingerprint_is_deterministic(self):
        boundary = LearningPromotionEligibilityBoundary()
        first = boundary.evaluate(self._request(), self._integrity())
        second = boundary.evaluate(self._request(), self._integrity())
        self.assertEqual(first["eligibility_fingerprint"], second["eligibility_fingerprint"])
        self.assertEqual(
            first,
            json.loads(json.dumps(first, sort_keys=True)),
        )

    def test_invalid_quality_score_is_rejected(self):
        with self.assertRaises(LearningPromotionEligibilityError):
            LearningPromotionEligibilityBoundary().evaluate(self._request(quality_score=1.1), self._integrity())


if __name__ == "__main__":
    unittest.main()
