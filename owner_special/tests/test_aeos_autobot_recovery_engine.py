#!/usr/bin/env python3
"""Negative assurance for bounded AEOS HOLD recovery."""
from __future__ import annotations

import unittest

from tools.aeos_autobot_recovery_engine import (
    HoldRecord,
    RecoveryResult,
    RecoveryState,
    authorize_recovery,
    classify_hold,
    plan_recovery,
    recovery_evidence_id,
    reverify,
    run_bounded_recovery,
)


SHA = "a" * 40
EVIDENCE = "b" * 64


def hold() -> HoldRecord:
    return HoldRecord("hold-1", "iteration-1", SHA, "NEW_REGRESSION", "blocking failure", (EVIDENCE,))


class RecoveryEngineTests(unittest.TestCase):
    def test_classification_requires_blocker_evidence(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing_or_invalid_blocker_evidence"):
            classify_hold(HoldRecord("h", "i", SHA, "NEW_REGRESSION", "x", ()))

    def test_wrong_source_is_rejected(self) -> None:
        bad = HoldRecord("hold-1", "iteration-1", "c" * 40, "NEW_REGRESSION", "blocking failure", (EVIDENCE,))
        with self.assertRaisesRegex(ValueError, "recovery_identity_mismatch"):
            authorize_recovery(plan_recovery(hold(), "retest", attempt=1, max_attempts=2), bad, "owner")

    def test_unauthorized_recovery_is_protected(self) -> None:
        result = run_bounded_recovery(hold(), "retest", max_attempts=2, authorized_by="", executor=lambda _: RecoveryResult.PASS, verifier=lambda _: RecoveryResult.PASS)
        self.assertEqual(result, RecoveryState.PROTECTED_HOLD)

    def test_failed_recovery_never_passes(self) -> None:
        result = run_bounded_recovery(hold(), "retest", max_attempts=1, authorized_by="owner", executor=lambda _: RecoveryResult.FAIL, verifier=lambda _: RecoveryResult.FAIL)
        self.assertEqual(result, RecoveryState.PROTECTED_HOLD)

    def test_conflict_is_protected(self) -> None:
        result = run_bounded_recovery(hold(), "retest", max_attempts=3, authorized_by="owner", executor=lambda _: RecoveryResult.PASS, verifier=lambda _: RecoveryResult.CONFLICT)
        self.assertEqual(result, RecoveryState.PROTECTED_HOLD)

    def test_exhausted_retries_are_protected(self) -> None:
        result = run_bounded_recovery(hold(), "retest", max_attempts=2, authorized_by="owner", executor=lambda _: RecoveryResult.FAIL, verifier=lambda _: RecoveryResult.FAIL)
        self.assertEqual(result, RecoveryState.PROTECTED_HOLD)

    def test_successful_reverification_releases_hold(self) -> None:
        result = run_bounded_recovery(hold(), "retest", max_attempts=2, authorized_by="owner", executor=lambda _: RecoveryResult.PASS, verifier=lambda _: RecoveryResult.PASS)
        self.assertEqual(result, RecoveryState.RELEASE_HOLD)

    def test_recovery_evidence_identity_is_deterministic(self) -> None:
        h = hold()
        left = recovery_evidence_id(h, "retest", 1, RecoveryResult.PASS)
        right = recovery_evidence_id(h, "retest", 1, RecoveryResult.PASS)
        self.assertEqual(left, right)
        self.assertEqual(len(left), 64)

    def test_merge_authority_is_absent(self) -> None:
        self.assertFalse(hasattr(run_bounded_recovery, "merge"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
