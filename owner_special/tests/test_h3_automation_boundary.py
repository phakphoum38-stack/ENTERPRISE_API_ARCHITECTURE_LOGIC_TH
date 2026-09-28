import unittest

from owner_special.research_os_friend.h3_automation_boundary import (
    H3AutomationBoundary,
    H3AutomationBoundaryError,
)


SHA = "c04d60b36d51eb8529a4c65a61c7d5a411e5fe85"


def snapshot(**updates):
    value = {
        "schema": "research-os-mission-control-unified-snapshot/v1",
        "owner_id": "owner-001",
        "read_only": True,
        "execution_authority": "FriendOrchestrator",
        "authorization_authority": "OwnerPolicy",
        "approval_authority": "ApprovalGate",
        "source_versions": {"evidence": "research-os-mission-control-evidence/v1"},
        "evidence_verification": {
            "schema": "research-os-h3-evidence-attestation/v1",
            "status": "PASS",
            "authoritative": True,
            "owner_id": "owner-001",
            "target_sha": SHA,
            "provenance": {
                "exact_sha": SHA,
                "status": "PASS",
                "authoritative": True,
            },
        },
        "source_sha": SHA,
    }
    value.update(updates)
    return value


class H3AutomationBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.boundary = H3AutomationBoundary()

    def test_valid_snapshot_allows_only_guarded_observation(self):
        result = self.boundary.assess(snapshot(), expected_sha=SHA, owner_id="owner-001")
        self.assertEqual(result["auto_mode"], "AUTO_GUARDED")
        self.assertEqual(result["decision"], "ALLOW_GUARDED_OBSERVATION")
        self.assertFalse(result["can_execute"])
        self.assertFalse(result["can_approve"])
        self.assertFalse(result["can_release"])
        self.assertFalse(result["can_merge"])
        self.assertFalse(result["can_dispatch"])

    def test_rejects_stale_sha(self):
        with self.assertRaises(H3AutomationBoundaryError):
            self.boundary.assess(snapshot(source_sha="b" * 40), expected_sha=SHA, owner_id="owner-001")

    def test_rejects_owner_mismatch(self):
        with self.assertRaises(H3AutomationBoundaryError):
            self.boundary.assess(snapshot(), expected_sha=SHA, owner_id="owner-002")

    def test_rejects_non_read_only_snapshot(self):
        with self.assertRaises(H3AutomationBoundaryError):
            self.boundary.assess(snapshot(read_only=False), expected_sha=SHA, owner_id="owner-001")

    def test_rejects_authority_drift(self):
        with self.assertRaises(H3AutomationBoundaryError):
            self.boundary.assess(snapshot(approval_authority="H3"), expected_sha=SHA, owner_id="owner-001")

    def test_requires_h2_evidence_binding(self):
        with self.assertRaises(H3AutomationBoundaryError):
            self.boundary.assess(snapshot(source_versions={}), expected_sha=SHA, owner_id="owner-001")

    def test_requires_authoritative_evidence_verification(self):
        with self.assertRaises(H3AutomationBoundaryError):
            self.boundary.assess(snapshot(evidence_verification=None), expected_sha=SHA, owner_id="owner-001")

    def test_rejects_pending_evidence_verification(self):
        attestation = dict(snapshot()["evidence_verification"])
        attestation["status"] = "PENDING"
        with self.assertRaises(H3AutomationBoundaryError):
            self.boundary.assess(snapshot(evidence_verification=attestation), expected_sha=SHA, owner_id="owner-001")

    def test_rejects_non_authoritative_evidence_verification(self):
        attestation = dict(snapshot()["evidence_verification"])
        attestation["authoritative"] = False
        with self.assertRaises(H3AutomationBoundaryError):
            self.boundary.assess(snapshot(evidence_verification=attestation), expected_sha=SHA, owner_id="owner-001")

    def test_rejects_evidence_target_sha_mismatch(self):
        attestation = dict(snapshot()["evidence_verification"])
        attestation["target_sha"] = "b" * 40
        with self.assertRaises(H3AutomationBoundaryError):
            self.boundary.assess(snapshot(evidence_verification=attestation), expected_sha=SHA, owner_id="owner-001")

    def test_rejects_provenance_sha_mismatch(self):
        attestation = dict(snapshot()["evidence_verification"])
        attestation["provenance"] = dict(attestation["provenance"], exact_sha="b" * 40)
        with self.assertRaises(H3AutomationBoundaryError):
            self.boundary.assess(snapshot(evidence_verification=attestation), expected_sha=SHA, owner_id="owner-001")

    def test_rejects_action_like_fields(self):
        with self.assertRaises(H3AutomationBoundaryError):
            self.boundary.assess(snapshot(merge=True), expected_sha=SHA, owner_id="owner-001")

    def test_rejects_nested_action_like_fields(self):
        with self.assertRaises(H3AutomationBoundaryError):
            self.boundary.assess(snapshot(details={"dispatch": "workflow"}), expected_sha=SHA, owner_id="owner-001")

    def test_rejects_excessive_depth(self):
        value = "leaf"
        for _ in range(10):
            value = {"nested": value}
        with self.assertRaises(H3AutomationBoundaryError):
            self.boundary.assess(snapshot(details=value), expected_sha=SHA, owner_id="owner-001")

    def test_assessment_is_deterministic(self):
        first = self.boundary.assess(snapshot(), expected_sha=SHA, owner_id="owner-001")
        second = self.boundary.assess(snapshot(), expected_sha=SHA, owner_id="owner-001")
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
