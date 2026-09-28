from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from .sandbox_test import SandboxTestResult


@dataclass(frozen=True)
class LearningEvidence:
    """Evidence record derived strictly from a completed sandbox test result."""

    evidence_id: str
    test_id: str
    sandbox_id: str
    result_hash: str
    passed: bool


class TestEvidenceBoundary:
    """Deterministic projection from TestResult to Evidence.

    This boundary does not execute candidates, rerun tests, invent observations,
    calculate confidence, promote skills, or mutate Core Skills.
    """

    def derive(self, result: SandboxTestResult) -> LearningEvidence:
        if not result.test_id or len(result.test_id) != 64:
            raise ValueError("test_id must be a SHA-256 identity")
        if not result.sandbox_id.strip():
            raise ValueError("sandbox_id is required")
        if not isinstance(result.passed, bool):
            raise ValueError("test result must declare boolean passed state")

        result_payload = {
            "test_id": result.test_id,
            "sandbox_id": result.sandbox_id,
            "passed": result.passed,
            "checks": result.checks,
            "failures": result.failures,
        }
        result_hash = hashlib.sha256(
            json.dumps(result_payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

        evidence_payload = {
            "type": "sandbox_test_result",
            "test_id": result.test_id,
            "sandbox_id": result.sandbox_id,
            "result_hash": result_hash,
            "passed": result.passed,
        }
        evidence_id = hashlib.sha256(
            json.dumps(evidence_payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

        return LearningEvidence(
            evidence_id=evidence_id,
            test_id=result.test_id,
            sandbox_id=result.sandbox_id,
            result_hash=result_hash,
            passed=result.passed,
        )
