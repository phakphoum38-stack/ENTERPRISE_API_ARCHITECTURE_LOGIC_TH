import unittest

from owner_special.research_os_friend.hold_recovery_engine import (
    Authorization,
    Hold,
    HoldClass,
    HoldDisposition,
    RecoveryEngine,
    RecoveryError,
    RecoveryPlan,
)


SHA = "c04d60b36d51eb8529a4c65a61c7d5a411e5fe85"
ITER = "iteration-001"
HOLD = "hold-001"


def make_hold():
    return Hold(HOLD, ITER, SHA, "CI blocker", {"id": "blocker-1"})


def make_auth(plan, authorized=True):
    return Authorization(
        plan.hold_id,
        plan.iteration_id,
        plan.source_sha,
        authorized,
        "owner-reviewer",
        "plan-fingerprint",
    )


class HoldRecoveryEngineTests(unittest.TestCase):
    def test_stale_source_is_protected_hold(self):
        engine = RecoveryEngine()
        hold = Hold(HOLD, ITER, "1" * 40, "stale", {"id": "b"})
        self.assertEqual(engine.classify(hold, expected_iteration_id=ITER, expected_source_sha=SHA), HoldClass.STALE_SOURCE)

    def test_wrong_iteration_is_protected_hold(self):
        engine = RecoveryEngine()
        hold = Hold(HOLD, "iteration-999", SHA, "wrong iteration", {"id": "b"})
        self.assertEqual(engine.classify(hold, expected_iteration_id=ITER, expected_source_sha=SHA), HoldClass.WRONG_ITERATION)

    def test_missing_blocker_evidence_is_protected_hold(self):
        engine = RecoveryEngine()
        self.assertEqual(
            engine.classify(make_hold(), expected_iteration_id=ITER, expected_source_sha=SHA, evidence=None),
            HoldClass.MISSING_BLOCKER_EVIDENCE,
        )

    def test_conflicting_evidence_is_protected_hold(self):
        engine = RecoveryEngine()
        self.assertEqual(
            engine.classify(make_hold(), expected_iteration_id=ITER, expected_source_sha=SHA, evidence={"conflict": True}),
            HoldClass.CONFLICTING_EVIDENCE,
        )

    def test_unauthorized_recovery_is_protected_hold(self):
        engine = RecoveryEngine()
        plan = RecoveryPlan(HOLD, ITER, SHA, HoldClass.TIMEOUT, 1)
        with self.assertRaises(RecoveryError):
            engine.execute(plan, make_auth(plan, authorized=False), lambda _: {"status": "PASS"})

    def test_failed_recovery_reclassifies_and_never_passes(self):
        engine = RecoveryEngine()
        hold = make_hold()
        plan = engine.recovery_plan(hold, HoldClass.TIMEOUT)
        attempt = engine.execute(plan, make_auth(plan), lambda _: {"status": "FAIL", "source_sha": SHA})
        self.assertEqual(attempt.status, "FAIL")
        self.assertEqual(
            engine.reverify(hold, attempt, {"status": "FAIL", "source_sha": SHA, "iteration_id": ITER, "hold_id": HOLD}),
            HoldDisposition.HOLD,
        )

    def test_exhausted_retries_are_protected_hold(self):
        engine = RecoveryEngine(max_attempts=2)
        hold = make_hold()
        for attempt_no in (1, 2):
            plan = engine.recovery_plan(hold, HoldClass.TIMEOUT)
            self.assertEqual(plan.attempt, attempt_no)
            attempt = engine.execute(plan, make_auth(plan), lambda _: {"status": "FAIL"})
            self.assertEqual(
                engine.reverify(hold, attempt, {"status": "FAIL", "source_sha": SHA, "iteration_id": ITER, "hold_id": HOLD}),
                HoldDisposition.PROTECTED_HOLD if attempt_no == 2 else HoldDisposition.HOLD,
            )

    def test_successful_reverification_releases_hold(self):
        engine = RecoveryEngine()
        hold = make_hold()
        plan = engine.recovery_plan(hold, HoldClass.TIMEOUT)
        attempt = engine.execute(plan, make_auth(plan), lambda _: {"status": "PASS"})
        self.assertEqual(
            engine.reverify(
                hold,
                attempt,
                {"status": "PASS", "authoritative": True, "source_sha": SHA, "iteration_id": ITER, "hold_id": HOLD},
            ),
            HoldDisposition.RELEASE_HOLD,
        )

    def test_reverification_rejects_stale_sha(self):
        engine = RecoveryEngine()
        hold = make_hold()
        plan = engine.recovery_plan(hold, HoldClass.TIMEOUT)
        attempt = engine.execute(plan, make_auth(plan), lambda _: {"status": "PASS"})
        self.assertEqual(
            engine.reverify(
                hold,
                attempt,
                {"status": "PASS", "authoritative": True, "source_sha": "1" * 40, "iteration_id": ITER, "hold_id": HOLD},
            ),
            HoldDisposition.PROTECTED_HOLD,
        )

    def test_reverification_rejects_wrong_iteration(self):
        engine = RecoveryEngine()
        hold = make_hold()
        plan = engine.recovery_plan(hold, HoldClass.TIMEOUT)
        attempt = engine.execute(plan, make_auth(plan), lambda _: {"status": "PASS"})
        self.assertEqual(
            engine.reverify(
                hold,
                attempt,
                {"status": "PASS", "authoritative": True, "source_sha": SHA, "iteration_id": "iteration-999", "hold_id": HOLD},
            ),
            HoldDisposition.PROTECTED_HOLD,
        )

    def test_reverification_conflict_never_releases(self):
        engine = RecoveryEngine()
        hold = make_hold()
        plan = engine.recovery_plan(hold, HoldClass.TIMEOUT)
        attempt = engine.execute(plan, make_auth(plan), lambda _: {"status": "PASS"})
        self.assertEqual(
            engine.reverify(
                hold,
                attempt,
                {"status": "PASS", "authoritative": True, "conflict": True, "source_sha": SHA, "iteration_id": ITER, "hold_id": HOLD},
            ),
            HoldDisposition.PROTECTED_HOLD,
        )

    def test_engine_has_no_merge_or_self_certification_authority(self):
        engine = RecoveryEngine()
        hold = make_hold()
        plan = engine.recovery_plan(hold, HoldClass.TIMEOUT)
        attempt = engine.execute(plan, make_auth(plan), lambda _: {"status": "PASS"})
        record = engine.audit_record(hold, attempt)
        self.assertFalse(record["merge_authority"])
        self.assertFalse(record["self_certification"])

    def test_execution_limit_is_bounded(self):
        engine = RecoveryEngine(max_execution_steps=2)
        plan = RecoveryPlan(HOLD, ITER, SHA, HoldClass.TIMEOUT, 1, execution_steps=3)
        with self.assertRaises(RecoveryError):
            engine.execute(plan, make_auth(plan), lambda _: {"status": "PASS"})

    def test_attempt_binding_cannot_be_crossed(self):
        engine = RecoveryEngine()
        hold = make_hold()
        plan = engine.recovery_plan(hold, HoldClass.TIMEOUT)
        attempt = engine.execute(plan, make_auth(plan), lambda _: {"status": "PASS"})
        other = Hold("hold-002", ITER, SHA, "different", {"id": "b"})
        self.assertEqual(
            engine.reverify(other, attempt, {"status": "PASS", "authoritative": True, "source_sha": SHA, "iteration_id": ITER, "hold_id": "hold-002"}),
            HoldDisposition.PROTECTED_HOLD,
        )


if __name__ == "__main__":
    unittest.main()
