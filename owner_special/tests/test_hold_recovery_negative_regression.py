import unittest

from owner_special.research_os_friend.hold_recovery_engine import (
    Authorization,
    Hold,
    HoldClass,
    HoldDisposition,
    RecoveryEngine,
    RecoveryError,
)


SHA_A = "a" * 40
SHA_B = "b" * 40
ITER_A = "iteration-a"
ITER_B = "iteration-b"
HOLD = "hold-negative-regression"


def hold(iteration=ITER_A, source_sha=SHA_A, evidence=None):
    return Hold(
        HOLD,
        iteration,
        source_sha,
        "negative regression blocker",
        evidence if evidence is not None else {"id": "blocker-1"},
    )


def auth(plan, *, authorized=True, actor="independent-verifier", fingerprint="fp"):
    return Authorization(
        plan.hold_id,
        plan.iteration_id,
        plan.source_sha,
        authorized,
        actor,
        fingerprint,
    )


class HoldRecoveryNegativeRootCauseSuite(unittest.TestCase):
    """Single adversarial suite covering F-001 through F-005 on the current PR head.

    These tests intentionally describe the constitutional behavior that the source fix
    must satisfy. On the current implementation several tests are expected to FAIL;
    that failure is the forensic evidence proving the five root causes remain present.
    """

    def test_f001_unknown_evidence_must_never_be_released(self):
        engine = RecoveryEngine()
        h = hold(evidence={"unrecognized": "payload"})
        classification = engine.classify(
            h,
            expected_iteration_id=ITER_A,
            expected_source_sha=SHA_A,
            evidence={"unrecognized": "payload"},
        )
        self.assertEqual(classification, HoldClass.UNKNOWN)
        plan = engine.recovery_plan(h, classification)
        self.assertEqual(plan.action, "protected_hold")

    def test_f001_unknown_plus_fake_pass_must_stay_protected(self):
        engine = RecoveryEngine()
        h = hold(evidence={"state": "banana"})
        classification = engine.classify(
            h,
            expected_iteration_id=ITER_A,
            expected_source_sha=SHA_A,
            evidence={"state": "banana"},
        )
        plan = engine.recovery_plan(h, classification)
        self.assertEqual(plan.action, "protected_hold")

    def test_f002_attempt_counter_isolation_by_iteration_and_source(self):
        engine = RecoveryEngine(max_attempts=2)
        h1 = hold(ITER_A, SHA_A)
        p1 = engine.recovery_plan(h1, HoldClass.TIMEOUT)
        a1 = engine.execute(p1, auth(p1), lambda _: {"status": "FAIL"})
        p2 = engine.recovery_plan(h1, HoldClass.TIMEOUT)
        engine.execute(p2, auth(p2), lambda _: {"status": "FAIL"})

        h2 = hold(ITER_B, SHA_B)
        fresh = engine.recovery_plan(h2, HoldClass.TIMEOUT)
        self.assertEqual(fresh.attempt, 1)
        self.assertNotEqual(a1.iteration_id, h2.iteration_id)
        self.assertNotEqual(a1.source_sha, h2.source_sha)

    def test_f003_missing_verifier_provenance_must_not_release(self):
        engine = RecoveryEngine()
        h = hold()
        p = engine.recovery_plan(h, HoldClass.TIMEOUT)
        attempt = engine.execute(p, auth(p), lambda _: {"status": "PASS"})
        verification_without_provenance = {
            "status": "PASS",
            "authoritative": True,
            "source_sha": SHA_A,
            "iteration_id": ITER_A,
            "hold_id": HOLD,
        }
        self.assertEqual(
            engine.reverify(h, attempt, verification_without_provenance),
            HoldDisposition.PROTECTED_HOLD,
        )

    def test_f003_wrong_verifier_identity_must_not_release(self):
        engine = RecoveryEngine()
        h = hold()
        p = engine.recovery_plan(h, HoldClass.TIMEOUT)
        engine.execute(p, auth(p), lambda _: {"status": "PASS"})
        verification = {
            "status": "PASS",
            "authoritative": True,
            "source_sha": SHA_A,
            "iteration_id": ITER_A,
            "hold_id": HOLD,
            "verifier_id": "unauthorized-verifier",
            "verifier_role": "owner",
            "evidence_id": "evidence-1",
            "digest": "digest-1",
        }
        # The source fix must bind release to the authorized independent verifier.
        self.assertEqual(engine.reverify(h, engine.attempts[-1], verification), HoldDisposition.PROTECTED_HOLD)

    def test_f004_unauthorized_recovery_must_emit_protected_hold_disposition(self):
        engine = RecoveryEngine()
        h = hold()
        p = engine.recovery_plan(h, HoldClass.TIMEOUT)
        try:
            result = engine.execute(p, auth(p, authorized=False), lambda _: {"status": "PASS"})
        except RecoveryError as exc:
            self.fail(f"unauthorized recovery must be deterministic PROTECTED_HOLD, not exception: {exc}")
        self.assertEqual(result.status, HoldDisposition.PROTECTED_HOLD.value)

    def test_f004_exhausted_recovery_must_emit_protected_hold_disposition(self):
        engine = RecoveryEngine(max_attempts=1)
        h = hold()
        p = engine.recovery_plan(h, HoldClass.TIMEOUT)
        engine.execute(p, auth(p), lambda _: {"status": "FAIL"})
        exhausted = engine.recovery_plan(h, HoldClass.TIMEOUT)
        try:
            result = engine.execute(exhausted, auth(exhausted), lambda _: {"status": "PASS"})
        except RecoveryError as exc:
            self.fail(f"exhausted recovery must be deterministic PROTECTED_HOLD, not exception: {exc}")
        self.assertEqual(result.status, HoldDisposition.PROTECTED_HOLD.value)

    def test_f005_malformed_evidence_must_not_become_unknown(self):
        engine = RecoveryEngine()
        malformed_inputs = [
            {"hello": "world"},
            {"state": "banana"},
            {"authorized": "yes"},
            {"anything": {"arbitrary": "data"}},
        ]
        for evidence in malformed_inputs:
            with self.subTest(evidence=evidence):
                classification = engine.classify(
                    hold(evidence=evidence),
                    expected_iteration_id=ITER_A,
                    expected_source_sha=SHA_A,
                    evidence=evidence,
                )
                self.assertNotEqual(classification, HoldClass.UNKNOWN)
                self.assertIn(
                    classification,
                    {
                        HoldClass.MISSING_BLOCKER_EVIDENCE,
                        HoldClass.CONFLICTING_EVIDENCE,
                        HoldClass.UNAUTHORIZED,
                        HoldClass.FAILED_RECOVERY,
                    },
                )

    def test_f005_conflicting_malformed_evidence_stays_protected(self):
        engine = RecoveryEngine()
        h = hold(evidence={"conflict": True, "unexpected": object()})
        classification = engine.classify(
            h,
            expected_iteration_id=ITER_A,
            expected_source_sha=SHA_A,
            evidence=h.blocker_evidence,
        )
        plan = engine.recovery_plan(h, classification)
        self.assertEqual(plan.action, "protected_hold")

    def test_positive_control_valid_independent_pass_can_release(self):
        engine = RecoveryEngine()
        h = hold()
        p = engine.recovery_plan(h, HoldClass.TIMEOUT)
        attempt = engine.execute(p, auth(p), lambda _: {"status": "PASS"})
        verification = {
            "status": "PASS",
            "authoritative": True,
            "source_sha": SHA_A,
            "iteration_id": ITER_A,
            "hold_id": HOLD,
            "verifier_id": "independent-verifier",
            "verifier_role": "independent-reviewer",
            "evidence_id": "evidence-1",
            "digest": "digest-1",
        }
        self.assertEqual(
            engine.reverify(h, attempt, verification),
            HoldDisposition.RELEASE_HOLD,
        )


if __name__ == "__main__":
    unittest.main()
