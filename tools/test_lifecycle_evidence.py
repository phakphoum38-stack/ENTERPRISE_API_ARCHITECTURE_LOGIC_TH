import tempfile
import unittest
from pathlib import Path

from tools.lifecycle_evidence import LifecycleEvidence, LifecycleEvidenceLedger


SHA = "a" * 40


def make(state: str, **kwargs: object) -> LifecycleEvidence:
    return LifecycleEvidence.create(
        correlation_id="corr-001",
        capability_id="friend",
        action="inspect status",
        state=state,
        owner_id="owner-001",
        source_sha=SHA,
        target_sha=SHA,
        workflow_run_id="workflow-001",
        **kwargs,
    )


class LifecycleEvidenceTests(unittest.TestCase):
    def test_required_evidence_fields_and_fingerprint(self) -> None:
        record = make("INTENT")
        self.assertTrue(record.event_id.startswith("ev-"))
        self.assertEqual(record.correlation_id, "corr-001")
        self.assertEqual(record.source_sha, SHA)
        self.assertEqual(record.target_sha, SHA)
        self.assertEqual(record.workflow_run_id, "workflow-001")
        self.assertEqual(record.project_id, "")
        self.assertEqual(len(record.fingerprint), 64)
        self.assertEqual(len(record.evidence_sha256), 64)

    def test_complete_lifecycle_validates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = LifecycleEvidenceLedger(Path(directory) / "evidence.jsonl")
            for state in (
                "INTENT", "VALIDATE", "PREPARE", "AUTHORIZE",
                "EXECUTE", "OBSERVE", "EVIDENCE", "COMPLETE",
            ):
                ledger.append(make(state))
            self.assertEqual(
                ledger.validate_chain(
                    correlation_id="corr-001", expected_source_sha=SHA
                ),
                (),
            )

    def test_failed_lifecycle_requires_explicit_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = LifecycleEvidenceLedger(Path(directory) / "evidence.jsonl")
            ledger.append(make("INTENT"))
            ledger.append(make("OBSERVE"))
            ledger.append(
                make(
                    "RECOVER",
                    recovery_required=True,
                    recovery_reason="executor-failed",
                )
            )
            self.assertEqual(
                ledger.validate_chain(
                    correlation_id="corr-001", expected_source_sha=SHA
                ),
                (),
            )

    def test_project_identity_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = LifecycleEvidenceLedger(Path(directory) / "evidence.jsonl")
            ledger.append(make("INTENT", project_id="project-001"))
            ledger.append(make("RECOVER", project_id="project-001", recovery_required=True, recovery_reason="test"))
            self.assertIn(
                "project identity mismatch",
                ledger.validate_chain(
                    correlation_id="corr-001",
                    expected_source_sha=SHA,
                    expected_project_id="project-002",
                ),
            )

    def test_source_sha_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = LifecycleEvidenceLedger(Path(directory) / "evidence.jsonl")
            ledger.append(make("INTENT"))
            ledger.append(
                make(
                    "RECOVER",
                    recovery_required=True,
                    recovery_reason="source-changed",
                )
            )
            self.assertIn(
                "source SHA mismatch",
                ledger.validate_chain(
                    correlation_id="corr-001", expected_source_sha="b" * 40
                ),
            )

    def test_recovery_without_reason_is_rejected(self) -> None:
        with self.assertRaises(ValueError) as raised:
            make("RECOVER", recovery_required=True)
        self.assertIn("recovery_reason", str(raised.exception))

    def test_module_does_not_execute_an_executor(self) -> None:
        self.assertFalse(hasattr(LifecycleEvidenceLedger, "execute"))
        self.assertFalse(hasattr(LifecycleEvidenceLedger, "authorize"))


if __name__ == "__main__":
    unittest.main()
