from __future__ import annotations

import unittest

from owner_special.research_os_friend.learning_final_lifecycle import (
    LearningFinalLifecycleBoundary,
    LearningFinalLifecycleError,
    LearningFinalLifecycleRequest,
)


class LearningFinalLifecycleBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.boundary = LearningFinalLifecycleBoundary()
        self.request = LearningFinalLifecycleRequest(
            owner="owner_special",
            skill_name="bounded-research",
            skill_version=1,
            promotion_record_fingerprint="a" * 64,
            correlation_id="corr-h27",
        )
        self.consumption = {
            "schema": "research-os-learning-skill-consumption/v1",
            "owner": "owner_special",
            "skill_name": "bounded-research",
            "skill_version": 1,
            "correlation_id": "corr-h27",
            "consumption_fingerprint": "b" * 64,
            "read_only": True,
            "authority": "none",
        }
        self.activation = {
            "schema": "research-os-learning-skill-activation/v1",
            "owner": "owner_special",
            "skill_name": "bounded-research",
            "skill_version": 1,
            "consumption_fingerprint": "b" * 64,
            "activation_fingerprint": "c" * 64,
            "read_only": True,
            "authority": "none",
        }
        self.result = {
            "schema": "research-os-learning-executor-result/v1",
            "owner": "owner_special",
            "skill_name": "bounded-research",
            "skill_version": 1,
            "correlation_id": "corr-h27",
            "activation_fingerprint": "c" * 64,
            "status": "SUCCEEDED",
            "executor_result_fingerprint": "d" * 64,
            "read_only": True,
            "authority": "none",
        }
        self.provenance = {
            "schema": "research-os-learning-evidence-provenance/v1",
            "owner": "owner_special",
            "skill_name": "bounded-research",
            "skill_version": 1,
            "correlation_id": "corr-h27",
            "executor_result_fingerprint": "d" * 64,
            "provenance_fingerprint": "e" * 64,
            "evidence_state": "BOUND_EXTERNAL_REFERENCES",
            "read_only": True,
            "authority": "none",
        }

    def test_successful_chain_completes_lifecycle(self) -> None:
        result = self.boundary.finalize(self.request, self.consumption, self.activation, self.result, self.provenance)
        self.assertEqual(result["schema"], "research-os-learning-final-lifecycle/v1")
        self.assertEqual(result["lifecycle_state"], "LEARNING_LIFECYCLE_COMPLETE")
        self.assertTrue(result["read_only"])
        self.assertEqual(result["authority"], "none")

    def test_failed_runtime_is_classified(self) -> None:
        runtime = dict(self.result, status="FAILED")
        result = self.boundary.finalize(self.request, self.consumption, self.activation, runtime, self.provenance)
        self.assertEqual(result["lifecycle_state"], "LEARNING_LIFECYCLE_FAILED")

    def test_blocked_runtime_is_classified(self) -> None:
        runtime = dict(self.result, status="BLOCKED")
        result = self.boundary.finalize(self.request, self.consumption, self.activation, runtime, self.provenance)
        self.assertEqual(result["lifecycle_state"], "LEARNING_LIFECYCLE_BLOCKED")

    def test_activation_consumption_binding_is_required(self) -> None:
        activation = dict(self.activation, consumption_fingerprint="f" * 64)
        with self.assertRaises(LearningFinalLifecycleError):
            self.boundary.finalize(self.request, self.consumption, activation, self.result, self.provenance)

    def test_result_activation_binding_is_required(self) -> None:
        runtime = dict(self.result, activation_fingerprint="f" * 64)
        with self.assertRaises(LearningFinalLifecycleError):
            self.boundary.finalize(self.request, self.consumption, self.activation, runtime, self.provenance)

    def test_provenance_result_binding_is_required(self) -> None:
        provenance = dict(self.provenance, executor_result_fingerprint="f" * 64)
        with self.assertRaises(LearningFinalLifecycleError):
            self.boundary.finalize(self.request, self.consumption, self.activation, self.result, provenance)

    def test_provenance_must_be_bound(self) -> None:
        provenance = dict(self.provenance, evidence_state="UNBOUND")
        with self.assertRaises(LearningFinalLifecycleError):
            self.boundary.finalize(self.request, self.consumption, self.activation, self.result, provenance)


if __name__ == "__main__":
    unittest.main()
