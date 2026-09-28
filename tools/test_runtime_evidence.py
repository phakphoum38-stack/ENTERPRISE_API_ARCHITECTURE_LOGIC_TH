import tempfile
import unittest
from pathlib import Path

from tools.lifecycle_evidence import LifecycleEvidenceLedger, LifecycleEvidence
from tools.runtime_evidence import capture_runtime_evidence

SHA = "a" * 40


class RuntimeEvidenceTests(unittest.TestCase):
    def test_snapshot_is_projection_not_a_second_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = LifecycleEvidenceLedger(Path(directory) / "evidence.jsonl")
            for state in (
                "INTENT", "VALIDATE", "PREPARE", "AUTHORIZE",
                "EXECUTE", "OBSERVE", "EVIDENCE", "COMPLETE",
            ):
                ledger.append(
                    LifecycleEvidence.create(
                        project_id="project-001",
                        correlation_id="corr-runtime",
                        capability_id="agent",
                        action="run agent",
                        state=state,
                        owner_id="owner-001",
                        source_sha=SHA,
                        target_sha=SHA,
                        workflow_run_id="workflow-001",
                    )
                )
            snapshot = capture_runtime_evidence(
                ledger,
                project_id="project-001",
                correlation_id="corr-runtime",
                expected_source_sha=SHA,
            )
            self.assertEqual(snapshot.terminal_state, "COMPLETE")
            self.assertIn('"project_id": "project-001"', snapshot.to_json())
            self.assertEqual(len(snapshot.records), 8)


if __name__ == "__main__":
    unittest.main()
