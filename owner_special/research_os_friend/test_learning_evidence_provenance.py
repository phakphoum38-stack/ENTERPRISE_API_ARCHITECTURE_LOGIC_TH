from __future__ import annotations

import unittest

from owner_special.research_os_friend.learning_evidence_provenance import (
    LearningEvidenceProvenanceBoundary,
    LearningEvidenceProvenanceError,
    LearningEvidenceProvenanceRequest,
)


class LearningEvidenceProvenanceBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.boundary = LearningEvidenceProvenanceBoundary()
        self.result = {
            "schema": "research-os-learning-executor-result/v1",
            "owner": "owner_special",
            "source_sha": "a" * 40,
            "skill_name": "bounded-research",
            "skill_version": 1,
            "correlation_id": "corr-h25",
            "status": "SUCCEEDED",
            "result": {"output": "ok"},
            "result_fingerprint": "b" * 64,
            "evidence_authority": "H26",
            "read_only": True,
            "authority": "none",
            "executor_result_fingerprint": "c" * 64,
        }
        self.request = LearningEvidenceProvenanceRequest(
            owner="owner_special",
            source_sha="a" * 40,
            skill_name="bounded-research",
            skill_version=1,
            correlation_id="corr-h25",
            executor_result_fingerprint="c" * 64,
            evidence_refs=("artifact://evidence/one", "ci://run/123"),
        )

    def test_external_evidence_refs_are_bound(self) -> None:
        result = self.boundary.bind(self.request, self.result)
        self.assertEqual(result["schema"], "research-os-learning-evidence-provenance/v1")
        self.assertEqual(result["evidence_state"], "BOUND_EXTERNAL_REFERENCES")
        self.assertEqual(result["final_lifecycle_authority"], "H27")
        self.assertEqual(result["evidence_refs"], self.request.evidence_refs)
        self.assertTrue(result["read_only"])

    def test_missing_evidence_is_rejected(self) -> None:
        request = LearningEvidenceProvenanceRequest(
            owner=self.request.owner,
            source_sha=self.request.source_sha,
            skill_name=self.request.skill_name,
            skill_version=self.request.skill_version,
            correlation_id=self.request.correlation_id,
            executor_result_fingerprint=self.request.executor_result_fingerprint,
            evidence_refs=(),
        )
        with self.assertRaises(LearningEvidenceProvenanceError):
            self.boundary.bind(request, self.result)

    def test_executor_identity_mismatch_is_rejected(self) -> None:
        request = LearningEvidenceProvenanceRequest(
            owner=self.request.owner,
            source_sha=self.request.source_sha,
            skill_name="other",
            skill_version=1,
            correlation_id=self.request.correlation_id,
            executor_result_fingerprint=self.request.executor_result_fingerprint,
            evidence_refs=self.request.evidence_refs,
        )
        with self.assertRaises(LearningEvidenceProvenanceError):
            self.boundary.bind(request, self.result)

    def test_invalid_result_authority_is_rejected(self) -> None:
        result = dict(self.result)
        result["authority"] = "H26"
        with self.assertRaises(LearningEvidenceProvenanceError):
            self.boundary.bind(self.request, result)

    def test_unsafe_evidence_reference_is_rejected(self) -> None:
        request = LearningEvidenceProvenanceRequest(
            owner=self.request.owner,
            source_sha=self.request.source_sha,
            skill_name=self.request.skill_name,
            skill_version=self.request.skill_version,
            correlation_id=self.request.correlation_id,
            executor_result_fingerprint=self.request.executor_result_fingerprint,
            evidence_refs=("execute subprocess",),
        )
        with self.assertRaises(LearningEvidenceProvenanceError):
            self.boundary.bind(request, self.result)

    def test_too_many_evidence_refs_are_rejected(self) -> None:
        request = LearningEvidenceProvenanceRequest(
            owner=self.request.owner,
            source_sha=self.request.source_sha,
            skill_name=self.request.skill_name,
            skill_version=self.request.skill_version,
            correlation_id=self.request.correlation_id,
            executor_result_fingerprint=self.request.executor_result_fingerprint,
            evidence_refs=tuple(f"artifact://e/{i}" for i in range(65)),
        )
        with self.assertRaises(LearningEvidenceProvenanceError):
            self.boundary.bind(request, self.result)


if __name__ == "__main__":
    unittest.main()
