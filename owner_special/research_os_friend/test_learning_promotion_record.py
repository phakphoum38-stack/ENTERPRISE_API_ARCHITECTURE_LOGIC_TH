from __future__ import annotations

import unittest

from owner_special.research_os_friend.learning_promotion_record import (
    LearningPromotionRecordBoundary,
    LearningPromotionRecordError,
    LearningPromotionRecordRequest,
)


class LearningPromotionRecordBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.boundary = LearningPromotionRecordBoundary()
        self.eligibility = {
            "schema": "research-os-learning-promotion-eligibility/v1",
            "owner": "owner_special",
            "source_sha": "a" * 40,
            "correlation_id": "corr-h21",
            "skill_fingerprint": "b" * 64,
            "result_fingerprint": "c" * 64,
            "candidate_version": 1,
            "binding_fingerprint": "d" * 64,
            "eligibility_fingerprint": "e" * 64,
            "promotion_eligibility": "ELIGIBLE_FOR_H10",
            "promotion_authority": "H10",
            "candidate": {"skill": "bounded-research", "result": {"status": "SUCCEEDED"}},
            "read_only": True,
            "authority": "none",
        }

    def _request(self, **overrides: object) -> LearningPromotionRecordRequest:
        values = {
            "owner": "owner_special",
            "source_sha": "a" * 40,
            "correlation_id": "corr-h21",
            "skill_fingerprint": "b" * 64,
            "result_fingerprint": "c" * 64,
            "candidate_version": 1,
            "binding_fingerprint": "d" * 64,
            "eligibility_fingerprint": "e" * 64,
            "record_id": "record-h21-001",
        }
        values.update(overrides)
        return LearningPromotionRecordRequest(**values)

    def test_eligible_candidate_creates_ready_record(self) -> None:
        record = self.boundary.create(self._request(), self.eligibility)
        self.assertEqual(record["schema"], "research-os-learning-promotion-record/v1")
        self.assertEqual(record["record_state"], "READY_FOR_H10")
        self.assertEqual(record["promotion_authority"], "H10")
        self.assertTrue(record["read_only"])
        self.assertEqual(record["authority"], "none")
        self.assertEqual(record["candidate"], self.eligibility["candidate"])
        self.assertRegex(record["record_fingerprint"], r"^[0-9a-f]{64}$")

    def test_record_is_deterministic(self) -> None:
        request = self._request()
        first = self.boundary.create(request, self.eligibility)
        second = self.boundary.create(request, self.eligibility)
        self.assertEqual(first, second)

    def test_non_eligible_candidate_is_rejected(self) -> None:
        eligibility = dict(self.eligibility)
        eligibility["promotion_eligibility"] = "NOT_ELIGIBLE"
        with self.assertRaises(LearningPromotionRecordError):
            self.boundary.create(self._request(), eligibility)

    def test_identity_mismatch_is_rejected(self) -> None:
        request = self._request(correlation_id="wrong-correlation")
        with self.assertRaises(LearningPromotionRecordError):
            self.boundary.create(request, self.eligibility)

    def test_eligibility_fingerprint_mismatch_is_rejected(self) -> None:
        request = self._request(eligibility_fingerprint="f" * 64)
        with self.assertRaises(LearningPromotionRecordError):
            self.boundary.create(request, self.eligibility)

    def test_authority_contract_is_read_only(self) -> None:
        eligibility = dict(self.eligibility)
        eligibility["authority"] = "H10"
        with self.assertRaises(LearningPromotionRecordError):
            self.boundary.create(self._request(), eligibility)

    def test_unsafe_candidate_is_rejected(self) -> None:
        eligibility = dict(self.eligibility)
        eligibility["candidate"] = {"notes": "execute subprocess"}
        with self.assertRaises(LearningPromotionRecordError):
            self.boundary.create(self._request(), eligibility)

    def test_invalid_record_id_is_rejected(self) -> None:
        with self.assertRaises(LearningPromotionRecordError):
            self.boundary.create(self._request(record_id="secret-token"), self.eligibility)


if __name__ == "__main__":
    unittest.main()
