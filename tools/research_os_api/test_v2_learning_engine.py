#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest

from v2_brain_core import ActivityLedger
from v2_learning_engine import LearningEngine


class LearningEngineTests(unittest.TestCase):
    def test_records_structured_outcome_without_self_modification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            engine = LearningEngine(ActivityLedger(tmp))
            event = engine.record_experience(
                session_id="learning-session",
                task_id="task-1",
                objective="debug the build",
                status="verified",
                capabilities=("debug", "build"),
                skill_ids=("software.debug-diagnosis",),
                tool_ids=("workspace.build.inspect",),
                evidence_refs=("commit:abc", "workflow:123"),
                verification={"verified": True},
            )
            payload = event["payload"]
            self.assertEqual("verified", payload["status"])
            self.assertNotIn("raw_prompt", payload)
            self.assertNotIn("raw_response", payload)
            self.assertFalse(payload["learning_policy"]["hidden_reasoning_capture"])
            self.assertFalse(payload["learning_policy"]["self_modification"])
            self.assertFalse(engine.dashboard()["model_weight_update"])

    def test_secret_shapes_are_redacted_before_ledger_persistence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = ActivityLedger(tmp)
            engine = LearningEngine(ledger)
            engine.record_experience(
                session_id="learning-secret",
                task_id="task-secret",
                objective="inspect sk-abcdefghijklmnopqrst and continue",
                status="failed",
                blockers=("Bearer abcdefghijklmnopqrstuvwxyz",),
                verification={"api_key": "must-not-persist"},
            )
            text = ledger.path.read_text(encoding="utf-8")
            self.assertNotIn("sk-abcdefghijklmnopqrst", text)
            self.assertNotIn("abcdefghijklmnopqrstuvwxyz", text)
            self.assertNotIn("must-not-persist", text)
            self.assertIn("[REDACTED]", text)

    def test_patterns_aggregate_repeated_failures_and_generate_review_only_proposal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            engine = LearningEngine(ActivityLedger(tmp))
            for index in range(3):
                engine.record_experience(
                    session_id=f"session-{index}",
                    task_id=f"task-{index}",
                    status="verification_failed",
                    capabilities=("debug",),
                    skill_ids=("software.debug-diagnosis",),
                    blockers=("missing exact-SHA evidence",),
                    failure_category="evidence_gap",
                )
            patterns = engine.patterns()
            self.assertEqual(3, patterns["experience_count"])
            self.assertEqual(3, patterns["status_counts"]["verification_failed"])
            self.assertEqual(3, patterns["skill_outcomes"]["software.debug-diagnosis"]["verification_failed"])
            proposals = engine.refinement_proposals(minimum_repeats=2)
            self.assertGreaterEqual(len(proposals), 2)
            self.assertTrue(all(not item["automatic_change"] for item in proposals))
            self.assertTrue(all(item["review_required"] for item in proposals))

    def test_rejects_non_terminal_outcome(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            engine = LearningEngine(ActivityLedger(tmp))
            with self.assertRaisesRegex(ValueError, "unsupported learning outcome"):
                engine.record_experience(
                    session_id="learning-running",
                    task_id="task-running",
                    status="running",
                )


if __name__ == "__main__":
    unittest.main()
