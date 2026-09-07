import unittest

from owner_special.research_os_friend.evidence_provenance import EvidenceRecord, ProvenanceChain, ProvenanceError
from owner_special.research_os_friend.mission_control_desktop_contract import (
    MissionControlDesktopContract,
    MissionControlDesktopError,
)


SHA = "a" * 40


def record(**overrides):
    values = {
        "schema": "research-os.evidence.v1",
        "evidence_type": "ci-result",
        "source_sha": SHA,
        "producer": "github-actions",
        "correlation_id": "run-001",
        "observed_at": "2026-09-08T00:00:00Z",
        "payload": {"workflow": "ci", "conclusion": "success"},
    }
    values.update(overrides)
    return EvidenceRecord(**values)


class MissionControlDesktopContractTests(unittest.TestCase):
    def setUp(self):
        self.contract = MissionControlDesktopContract()

    def test_projects_exact_identity_as_read_only(self):
        result = self.contract.project(
            record(),
            owner_id="owner-special",
            expected_sha=SHA,
            current_correlation_id="run-001",
            status="PASS",
            summary={"workflow": "ci", "conclusion": "success"},
        )
        self.assertEqual(result["source_sha"], SHA)
        self.assertEqual(result["correlation_id"], "run-001")
        self.assertTrue(result["read_only"])
        self.assertEqual(result["status"], "PASS")

    def test_stale_sha_is_rejected(self):
        with self.assertRaises(MissionControlDesktopError):
            self.contract.project(
                record(), owner_id="owner-special", expected_sha="b" * 40, current_correlation_id="run-001"
            )

    def test_stale_correlation_is_rejected(self):
        with self.assertRaises(MissionControlDesktopError):
            self.contract.project(
                record(), owner_id="owner-special", expected_sha=SHA, current_correlation_id="run-002"
            )

    def test_provenance_must_terminate_at_record(self):
        chain = ProvenanceChain((record(),))
        other = record(evidence_type="gate-result")
        with self.assertRaises(MissionControlDesktopError):
            self.contract.project(
                other,
                owner_id="owner-special",
                expected_sha=SHA,
                current_correlation_id="run-001",
                provenance=chain,
            )

    def test_provenance_is_accepted_when_linked(self):
        first = record()
        chain = ProvenanceChain((first,))
        second = record(evidence_type="gate-result")
        chain = chain.append(second)
        result = self.contract.project(
            chain.records[-1],
            owner_id="owner-special",
            expected_sha=SHA,
            current_correlation_id="run-001",
            provenance=chain,
            status="FAIL",
        )
        self.assertEqual(result["provenance_fingerprint"], chain.fingerprint)

    def test_unknown_status_is_explicit(self):
        with self.assertRaises(MissionControlDesktopError):
            self.contract.project(
                record(), owner_id="owner-special", expected_sha=SHA, current_correlation_id="run-001", status="MAYBE"
            )

    def test_secret_like_summary_is_rejected(self):
        with self.assertRaises(MissionControlDesktopError):
            self.contract.project(
                record(),
                owner_id="owner-special",
                expected_sha=SHA,
                current_correlation_id="run-001",
                summary={"api_key": "secret"},
            )

    def test_authority_like_summary_is_rejected(self):
        with self.assertRaises(MissionControlDesktopError):
            self.contract.project(
                record(),
                owner_id="owner-special",
                expected_sha=SHA,
                current_correlation_id="run-001",
                summary={"release": "ready"},
            )

    def test_dynamic_values_are_rejected(self):
        with self.assertRaises(MissionControlDesktopError):
            self.contract.project(
                record(),
                owner_id="owner-special",
                expected_sha=SHA,
                current_correlation_id="run-001",
                summary={"value": object()},
            )

    def test_result_is_defensive_copy(self):
        result = self.contract.project(
            record(),
            owner_id="owner-special",
            expected_sha=SHA,
            current_correlation_id="run-001",
            summary={"items": ["one"]},
        )
        result["summary"]["items"].append("two")
        second = self.contract.project(
            record(),
            owner_id="owner-special",
            expected_sha=SHA,
            current_correlation_id="run-001",
            summary={"items": ["one"]},
        )
        self.assertEqual(second["summary"]["items"], ["one"])


if __name__ == "__main__":
    unittest.main()
