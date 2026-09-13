from __future__ import annotations

import unittest

from owner_special.research_os_friend.executor_result_boundary import (
    ExecutorResultBoundary,
    ExecutorResultError,
    ExecutorResultRequest,
)

OWNER = "owner_special"
SOURCE_SHA = "a" * 40
CORRELATION = "corr-h15"
SKILL_FP = "b" * 64
HANDOFF_FP = "c" * 64


def handoff() -> dict:
    return {
        "schema": "research-os-executor-handoff/v1",
        "owner": OWNER,
        "source_sha": SOURCE_SHA,
        "correlation_id": CORRELATION,
        "skill_fingerprint": SKILL_FP,
        "activation_decision": "ALLOW_ACTIVATION",
        "capability": "LEARNED_SKILL_EXECUTOR",
        "skill": {"name": "bounded research skill"},
        "handoff": "HANDOFF_READY",
        "read_only": True,
        "authority": "none",
        "handoff_fingerprint": HANDOFF_FP,
    }


def request(status="SUCCEEDED", result=None, **overrides) -> ExecutorResultRequest:
    values = {
        "owner": OWNER,
        "source_sha": SOURCE_SHA,
        "correlation_id": CORRELATION,
        "skill_fingerprint": SKILL_FP,
        "handoff_fingerprint": HANDOFF_FP,
        "status": status,
        "result": result or {"summary": "completed"},
    }
    values.update(overrides)
    return ExecutorResultRequest(**values)


class ExecutorResultBoundaryTests(unittest.TestCase):
    def test_successful_result_is_accepted_as_read_only_evidence(self) -> None:
        result = ExecutorResultBoundary().accept(request(), handoff())
        self.assertEqual(result["status"], "SUCCEEDED")
        self.assertTrue(result["read_only"])
        self.assertEqual(result["authority"], "none")

    def test_failed_and_blocked_results_are_preserved(self) -> None:
        boundary = ExecutorResultBoundary()
        self.assertEqual(boundary.accept(request("FAILED"), handoff())["status"], "FAILED")
        self.assertEqual(boundary.accept(request("BLOCKED"), handoff())["status"], "BLOCKED")

    def test_identity_mismatch_fails_closed(self) -> None:
        with self.assertRaises(ExecutorResultError):
            ExecutorResultBoundary().accept(request(source_sha="d" * 40), handoff())

    def test_handoff_fingerprint_mismatch_fails_closed(self) -> None:
        with self.assertRaises(ExecutorResultError):
            ExecutorResultBoundary().accept(request(handoff_fingerprint="d" * 64), handoff())

    def test_invalid_handoff_authority_fails_closed(self) -> None:
        invalid = handoff()
        invalid["authority"] = "executor"
        with self.assertRaises(ExecutorResultError):
            ExecutorResultBoundary().accept(request(), invalid)

    def test_secret_like_result_fails_closed(self) -> None:
        with self.assertRaises(ExecutorResultError):
            ExecutorResultBoundary().accept(request(result={"value": "sk-proj-secret"}), handoff())

    def test_result_snapshot_is_detached_and_deterministic(self) -> None:
        boundary = ExecutorResultBoundary()
        first = boundary.accept(request(), handoff())
        first["result"]["summary"] = "mutated"
        second = boundary.accept(request(), handoff())
        self.assertEqual(second["result"]["summary"], "completed")
        self.assertEqual(first["result_fingerprint"], second["result_fingerprint"])


if __name__ == "__main__":
    unittest.main()
