"""Regression tests for P0-1 canonical identity federation."""

from __future__ import annotations

import unittest

from owner_special.research_os_friend.canonical_identity_federation import (
    CanonicalIdentity,
    CanonicalIdentityError,
    assert_same_lineage,
    identity_from_mapping,
)


SHA_A = "a" * 40
SHA_B = "b" * 40


class CanonicalIdentityFederationTests(unittest.TestCase):
    def test_root_identity_requires_mission_work_and_baseline(self) -> None:
        identity = CanonicalIdentity("M1", "W1", SHA_A)
        self.assertEqual(identity.task_id, None)
        self.assertEqual(identity.work_id, "W1")

    def test_child_identity_requires_parent_identity(self) -> None:
        with self.assertRaisesRegex(CanonicalIdentityError, "task_id is required"):
            CanonicalIdentity("M1", "W1", SHA_A, run_id="R1")

        with self.assertRaisesRegex(CanonicalIdentityError, "run_id is required"):
            CanonicalIdentity("M1", "W1", SHA_A, task_id="T1", attempt_id="A1")

    def test_binding_is_immutable_and_progressive(self) -> None:
        root = CanonicalIdentity("M1", "W1", SHA_A)
        task = root.bind(task_id="T1")
        run = task.bind(run_id="R1")
        attempt = run.bind(attempt_id="A1")
        request = attempt.bind(request_id="REQ1")

        self.assertIsNone(root.task_id)
        self.assertEqual(task.task_id, "T1")
        self.assertEqual(run.run_id, "R1")
        self.assertEqual(attempt.attempt_id, "A1")
        self.assertEqual(request.request_id, "REQ1")

    def test_resource_admission_requires_attempt_and_request(self) -> None:
        identity = CanonicalIdentity(
            "M1", "W1", SHA_A, task_id="T1", run_id="R1", attempt_id="A1"
        )
        with self.assertRaisesRegex(
            CanonicalIdentityError, "request_id is required"
        ):
            identity.bind(admission_id="AD1")

        bound = identity.bind(request_id="REQ1", admission_id="AD1")
        self.assertEqual(bound.admission_id, "AD1")

    def test_artifact_requires_evidence(self) -> None:
        identity = CanonicalIdentity("M1", "W1", SHA_A, task_id="T1", run_id="R1")
        with self.assertRaisesRegex(CanonicalIdentityError, "evidence_id is required"):
            identity.bind(artifact_id="ART1")

        bound = identity.bind(evidence_id="E1", artifact_id="ART1")
        self.assertEqual(bound.artifact_id, "ART1")

    def test_mapping_adapter_preserves_existing_ids(self) -> None:
        identity = identity_from_mapping(
            {
                "mission_id": "M1",
                "work_id": "W1",
                "baseline_sha": SHA_A,
                "task_id": "T1",
                "run_id": "R1",
                "attempt_id": "A1",
            }
        )
        self.assertEqual(identity.as_mapping()["attempt_id"], "A1")

    def test_fingerprint_is_deterministic(self) -> None:
        left = CanonicalIdentity("M1", "W1", SHA_A, task_id="T1")
        right = CanonicalIdentity("M1", "W1", SHA_A, task_id="T1")
        self.assertEqual(left.fingerprint(), right.fingerprint())

    def test_lineage_conflicts_fail_closed(self) -> None:
        left = CanonicalIdentity("M1", "W1", SHA_A)
        with self.assertRaisesRegex(
            CanonicalIdentityError, "baseline_sha lineage conflict"
        ):
            assert_same_lineage(left, CanonicalIdentity("M1", "W1", SHA_B))

    def test_decision_can_bind_at_work_level(self) -> None:
        identity = CanonicalIdentity("M1", "W1", SHA_A).bind(decision_id="D1")
        self.assertEqual(identity.decision_id, "D1")


if __name__ == "__main__":
    unittest.main()
