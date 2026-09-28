import unittest

from owner_special.research_os_friend.self_learning import SelfLearningEngine
from owner_special.research_os_friend.self_learning_contract import (
    SelfLearningContract,
    SelfLearningContractError,
)


SOURCE_SHA = "0123456789abcdef0123456789abcdef01234567"


class SelfLearningContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = SelfLearningEngine()
        self.contract = SelfLearningContract(
            self.engine,
            owner_id="owner-h5",
            source_sha=SOURCE_SHA,
        )

    def test_snapshot_is_bounded_and_read_only(self) -> None:
        snapshot = self.contract.snapshot()
        self.assertEqual(snapshot["schema"], "research-os-self-learning/v1")
        self.assertEqual(snapshot["owner_id"], "owner-h5")
        self.assertEqual(snapshot["source_sha"], SOURCE_SHA)
        self.assertTrue(snapshot["read_only"])

    def test_evidence_is_required(self) -> None:
        with self.assertRaises(SelfLearningContractError):
            self.contract.propose_and_promote(
                name="verified-skill",
                goal="repeat a verified operation",
                procedure=("inspect", "validate"),
                evidence=(),
                confidence=0.95,
                run_correlation_id="h5.test.run",
            )

    def test_valid_evidence_can_promote(self) -> None:
        result = self.contract.propose_and_promote(
            name="verified-skill",
            goal="repeat a verified operation",
            procedure=("inspect", "validate"),
            evidence=("ci-pass", "verified-result"),
            confidence=0.95,
            run_correlation_id="h5.test.run",
        )
        self.assertIsNotNone(result)
        assert result is not None
        self.assertTrue(result["promoted"])
        self.assertFalse(result["core_mutation"])
        self.assertEqual(result["source_sha"], SOURCE_SHA)

    def test_low_confidence_candidate_is_not_promoted(self) -> None:
        result = self.contract.propose_and_promote(
            name="weak-skill",
            goal="insufficient confidence",
            procedure=("inspect",),
            evidence=("observed",),
            confidence=0.1,
            run_correlation_id="h5.test.run",
        )
        self.assertIsNone(result)

    def test_secret_like_learning_content_is_rejected(self) -> None:
        with self.assertRaises(SelfLearningContractError):
            self.contract.propose_and_promote(
                name="unsafe",
                goal="do not store secrets",
                procedure=("inspect",),
                evidence=("api_key=blocked",),
                confidence=0.95,
                run_correlation_id="h5.test.run",
            )

    def test_authority_like_learning_content_is_rejected(self) -> None:
        with self.assertRaises(SelfLearningContractError):
            self.contract._validate_payload({"release": "approve"})

    def test_dynamic_learning_content_is_rejected(self) -> None:
        with self.assertRaises(SelfLearningContractError):
            self.contract._validate_payload({"procedure": (lambda: None,)})

    def test_invalid_source_sha_is_rejected(self) -> None:
        with self.assertRaises(SelfLearningContractError):
            SelfLearningContract(
                self.engine,
                owner_id="owner-h5",
                source_sha="not-a-sha",
            )

    def test_invalid_correlation_is_rejected(self) -> None:
        with self.assertRaises(SelfLearningContractError):
            self.contract.propose_and_promote(
                name="verified-skill",
                goal="repeat a verified operation",
                procedure=("inspect",),
                evidence=("ci-pass",),
                confidence=0.95,
                run_correlation_id="bad correlation",
            )

    def test_snapshot_is_defensively_copied(self) -> None:
        self.contract.propose_and_promote(
            name="verified-skill",
            goal="repeat a verified operation",
            procedure=("inspect", "validate"),
            evidence=("ci-pass",),
            confidence=0.95,
            run_correlation_id="h5.test.run",
        )
        first = self.contract.snapshot()
        first["learning"]["approved_skills"][0]["name"] = "mutated"
        second = self.contract.snapshot()
        self.assertEqual(
            second["learning"]["approved_skills"][0]["name"],
            "verified-skill",
        )


if __name__ == "__main__":
    unittest.main()
