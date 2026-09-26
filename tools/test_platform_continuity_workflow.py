from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.lifecycle_evidence import LifecycleEvidenceLedger
from tools.platform_continuity_workflow import (
    build_successor_handoff,
    dispatch_checkpoint,
)
from tools.platform_work_checkpoint import create_checkpoint
from v3.research_os_v3.queue import DurableTaskQueue
from v3.research_os_v3.runner import StatelessResearchRunner


class PlatformContinuityWorkflowTests(unittest.TestCase):
    def test_checkpoint_to_queue_runner_evidence_and_successor(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            os.environ["RESEARCH_OS_DATA_DIR"] = str(root / "data")
            try:
                sha = "a" * 40
                with patch("tools.platform_work_checkpoint.canonical_sha", return_value=sha):
                    checkpoint = create_checkpoint(
                        owner_id="owner",
                        task_id="continuity-001",
                        workflow_state="ACTIVE",
                        current_step="platform-continuity",
                        pending_steps=["workflow-dispatch"],
                        context_refs=["current/RESEARCH_OS_CONTEXT_RECOVERY.json"],
                        source_sha=sha,
                        next_action="dispatch",
                    )
                    queue = DurableTaskQueue(root / "queue.db")
                    ledger = LifecycleEvidenceLedger(root / "evidence.jsonl")
                    runner = StatelessResearchRunner(queue, max_attempts=2, worker_id="test-runner")

                    result = dispatch_checkpoint(
                        owner_id="owner",
                        checkpoint_id=checkpoint["checkpoint_id"],
                        queue=queue,
                        runner=runner,
                        ledger=ledger,
                        handler=lambda _task: None,
                    )
                    self.assertEqual(result.status, "COMPLETED")
                    self.assertEqual(result.runner_status, "completed")
                    self.assertIsNotNone(result.successor_checkpoint_id)
                    self.assertEqual(len(result.evidence_refs), 2)
                    self.assertEqual(
                        ledger.validate_chain(
                            correlation_id=f"continuity-{checkpoint['checkpoint_id']}",
                            expected_source_sha=sha,
                        ),
                        (),
                    )
            finally:
                os.environ.pop("RESEARCH_OS_DATA_DIR", None)

    def test_resume_is_fail_closed_on_sha_drift(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            os.environ["RESEARCH_OS_DATA_DIR"] = str(raw)
            try:
                checkpoint = create_checkpoint(
                    owner_id="owner",
                    task_id="continuity-002",
                    workflow_state="ACTIVE",
                    current_step="platform-continuity",
                    source_sha="a" * 40,
                    next_action="dispatch",
                )
                with patch("tools.platform_work_checkpoint.canonical_sha", return_value="b" * 40):
                    with self.assertRaises(ValueError):
                        dispatch_checkpoint(
                            owner_id="owner",
                            checkpoint_id=checkpoint["checkpoint_id"],
                            queue=DurableTaskQueue(Path(raw) / "queue.db"),
                            runner=StatelessResearchRunner(
                                DurableTaskQueue(Path(raw) / "queue2.db"),
                                worker_id="unused",
                            ),
                            ledger=LifecycleEvidenceLedger(Path(raw) / "evidence.jsonl"),
                            handler=lambda _task: None,
                        )
            finally:
                os.environ.pop("RESEARCH_OS_DATA_DIR", None)

    def test_successor_handoff_forces_recovery_and_reverification(self) -> None:
        handoff = build_successor_handoff(
            repository="repo",
            canonical_sha="a" * 40,
            protected_baseline_sha="b" * 40,
            active_work=["continuity"],
            deferred_work=["flutter"],
            decisions=["platform-first"],
            verified_truths=["chat-is-not-storage"],
            evidence_refs=["ev-1"],
            open_risks=["runtime-8788"],
            assumptions=[],
            unknowns=[],
            authority_boundaries=["final_gate"],
            tooling_state=["queue"],
            active_mission="platform",
            next_permitted_action="resume",
            forbidden_actions=["direct-main-write"],
        )
        self.assertTrue(handoff["successor_requires_context_recovery"])
        self.assertTrue(handoff["successor_requires_reverification"])
        self.assertFalse(handoff["inherits_certification"])
        self.assertEqual(handoff["deferred_work"], ["flutter"])


if __name__ == "__main__":
    unittest.main()
