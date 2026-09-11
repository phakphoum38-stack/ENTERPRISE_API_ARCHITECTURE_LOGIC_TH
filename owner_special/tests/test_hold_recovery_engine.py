import unittest

from owner_special.research_os_friend.hold_recovery_engine import (
    Authorization,
    Hold,
    HoldClass,
    HoldDisposition,
    RecoveryAttempt,
    RecoveryEngine,
    RecoveryError,
    RecoveryPlan,
)


SHA = "0ea2b391f91ee4878a1bc21d2c5563adfd5bc5b9"
ITER = "iteration-001"
HOLD = "hold-001"
FINGERPRINT = "plan-fingerprint"


def make_hold(hold_id=HOLD, iteration_id=ITER, source_sha=SHA):
    return Hold(hold_id, iteration_id, source_sha, "CI blocker", {"id": "blocker-1"})


def make_auth(plan, authorized=True, actor="owner-reviewer", fingerprint=FINGERPRINT):
    return Authorization(
        plan.hold_id,
        plan.iteration_id,
        plan.source_sha,
        authorized,
        actor,
        fingerprint,
    )


def verify(attempt, **overrides):
    evidence = {
        "status": "PASS",
        "authoritative": True,
        "source_sha": attempt.source_sha,
        "iteration_id": attempt.iteration_id,
        "hold_id": attempt.hold_id,
        "plan_fingerprint": attempt.plan_fingerprint,
    }
    evidence.update(overrides)
    return evidence


class HoldRecoveryEngineTests(unittest.TestCase):
    def test_stale_source_is_protected_hold(self):
        engine = RecoveryEngine()
        hold = make_hold(source_sha="1" * 40)
        self.assertEqual(
            engine.classify(hold, expected_iteration_id=ITER, expected_source_sha=SHA),
            HoldClass.STALE_SOURCE,
        )

    def test_wrong_iteration_is_protected_hold(self):
        engine = RecoveryEngine()
        hold = make_hold(iteration_id="iteration-999")
        self.assertEqual(
            engine.classify(hold, expected_iteration_id=ITER, expected_source_sha=SHA),
            HoldClass.WRONG_ITERATION,
        )

    def test_missing_blocker_evidence_is_protected_hold(self):
        engine = RecoveryEngine()
        self.assertEqual(
            engine.classify(make_hold(), expected_iteration_id=ITER, expected_source_sha=SHA, evidence=None),
            HoldClass.MISSING_BLOCKER_EVIDENCE,
        )

    def test_conflicting_evidence_is_protected_hold(self):
        engine = RecoveryEngine()
        self.assertEqual(
            engine.classify(
                make_hold(),
                expected_iteration_id=ITER,
                expected_source_sha=SHA,
                evidence={"conflict": True},
            ),
            HoldClass.CONFLICTING_EVIDENCE,
        )

    def test_unknown_is_never_pass_and_plan_is_protected_hold(self):
        engine = RecoveryEngine()
        hold = make_hold()
        classification = engine.classify(
            hold,
            expected_iteration_id=ITER,
            expected_source_sha=SHA,
            evidence={"unrecognized": "state"},
        )
        self.assertEqual(classification, HoldClass.UNKNOWN)
        plan = engine.recovery_plan(hold, classification)
        self.assertEqual(plan.action, "protected_hold")
        self.assertFalse(engine.authorize(plan, make_auth(plan)))
        with self.assertRaises(RecoveryError):
            engine.execute(plan, make_auth(plan), lambda _: {"status": "PASS"})
        self.assertEqual(len(engine.rejections), 1)
        self.assertEqual(engine.rejections[0].classification, HoldClass.UNKNOWN)

    def test_protected_classifications_are_rejected(self):
        engine = RecoveryEngine()
        for classification in (
            HoldClass.STALE_SOURCE,
            HoldClass.WRONG_ITERATION,
            HoldClass.MISSING_BLOCKER_EVIDENCE,
            HoldClass.CONFLICTING_EVIDENCE,
            HoldClass.UNAUTHORIZED,
            HoldClass.EXHAUSTED_ATTEMPTS,
            HoldClass.UNKNOWN,
        ):
            plan = RecoveryPlan(HOLD, ITER, SHA, classification, 1)
            self.assertFalse(engine.authorize(plan, make_auth(plan)))

    def test_retryable_blocker_states_can_be_reverified_but_cannot_directly_pass(self):
        engine = RecoveryEngine()
        for classification in (HoldClass.RUNNING, HoldClass.TIMEOUT, HoldClass.INFRA_FAILED, HoldClass.INCOMPLETE):
            plan = RecoveryPlan(HOLD, ITER, SHA, classification, 1)
            self.assertTrue(engine.authorize(plan, make_auth(plan)))
            attempt = engine.execute(plan, make_auth(plan), lambda _: {"status": "FAIL"})
            self.assertEqual(
                engine.reverify(make_hold(), attempt, verify(attempt, status="FAIL")),
                HoldDisposition.HOLD,
            )

    def test_unauthorized_recovery_is_protected_hold_and_emits_evidence(self):
        engine = RecoveryEngine()
        plan = RecoveryPlan(HOLD, ITER, SHA, HoldClass.TIMEOUT, 1)
        auth = make_auth(plan, authorized=False)
        with self.assertRaises(RecoveryError):
            engine.execute(plan, auth, lambda _: {"status": "PASS"})
        self.assertEqual(len(engine.rejections), 1)
        record = engine.rejection_audit_record(engine.rejections[0])
        self.assertEqual(record["status"], "REJECTED")
        self.assertEqual(record["hold_id"], HOLD)
        self.assertEqual(record["iteration_id"], ITER)
        self.assertEqual(record["source_sha"], SHA)
        self.assertFalse(record["merge_authority"])
        self.assertFalse(record["self_certification"])

    def test_unauthorized_recovery_requires_actor_and_fingerprint(self):
        engine = RecoveryEngine()
        plan = RecoveryPlan(HOLD, ITER, SHA, HoldClass.TIMEOUT, 1)
        bad = Authorization(HOLD, ITER, SHA, True, "", "")
        with self.assertRaises(RecoveryError):
            engine.execute(plan, bad, lambda _: {"status": "PASS"})
        self.assertEqual(len(engine.rejections), 1)

    def test_failed_recovery_reclassifies_and_never_passes(self):
        engine = RecoveryEngine()
        hold = make_hold()
        plan = engine.recovery_plan(hold, HoldClass.TIMEOUT)
        attempt = engine.execute(
            plan,
            make_auth(plan),
            lambda _: {"status": "FAIL", "source_sha": SHA},
        )
        self.assertEqual(attempt.status, "FAIL")
        self.assertEqual(engine.reclassify(attempt), HoldClass.FAILED_RECOVERY)
        self.assertEqual(
            engine.reverify(hold, attempt, verify(attempt, status="FAIL")),
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
                engine.reverify(hold, attempt, verify(attempt, status="FAIL")),
                HoldDisposition.PROTECTED_HOLD if attempt_no == 2 else HoldDisposition.HOLD,
            )

    def test_retry_budget_is_bound_to_hold_iteration_and_source(self):
        engine = RecoveryEngine(max_attempts=3)
        first = make_hold("hold-001", "iteration-001", SHA)
        second_iteration = make_hold("hold-001", "iteration-002", SHA)
        second_source = make_hold("hold-001", "iteration-001", "1" * 40)

        for _ in range(2):
            plan = engine.recovery_plan(first, HoldClass.TIMEOUT)
            engine.execute(plan, make_auth(plan), lambda _: {"status": "FAIL"})

        iteration_plan = engine.recovery_plan(second_iteration, HoldClass.TIMEOUT)
        source_plan = engine.recovery_plan(second_source, HoldClass.TIMEOUT)
        self.assertEqual(iteration_plan.attempt, 1)
        self.assertEqual(source_plan.attempt, 1)

    def test_successful_reverification_requires_matching_plan_fingerprint(self):
        engine = RecoveryEngine()
        hold = make_hold()
        plan = engine.recovery_plan(hold, HoldClass.TIMEOUT)
        attempt = engine.execute(plan, make_auth(plan, fingerprint="approved-plan"), lambda _: {"status": "PASS"})
        self.assertEqual(
            engine.reverify(hold, attempt, verify(attempt, plan_fingerprint="different-plan")),
            HoldDisposition.PROTECTED_HOLD,
        )

    def test_successful_reverification_releases_hold_with_exact_provenance(self):
        engine = RecoveryEngine()
        hold = make_hold()
        plan = engine.recovery_plan(hold, HoldClass.TIMEOUT)
        attempt = engine.execute(plan, make_auth(plan, fingerprint="approved-plan"), lambda _: {"status": "PASS"})
        self.assertEqual(
            engine.reverify(hold, attempt, verify(attempt)),
            HoldDisposition.RELEASE_HOLD,
        )

    def test_unknown_attempt_cannot_release_even_with_authoritative_pass(self):
        engine = RecoveryEngine()
        hold = make_hold()
        unknown_attempt = RecoveryAttempt(HOLD, ITER, SHA, 1, HoldClass.UNKNOWN, "PASS", 1, {}, FINGERPRINT)
        self.assertEqual(
            engine.reverify(hold, unknown_attempt, {
                "status": "PASS",
                "authoritative": True,
                "source_sha": SHA,
                "iteration_id": ITER,
                "hold_id": HOLD,
                "plan_fingerprint": FINGERPRINT,
            }),
            HoldDisposition.PROTECTED_HOLD,
        )

    def test_reverification_rejects_stale_sha(self):
        engine = RecoveryEngine()
        hold = make_hold()
        plan = engine.recovery_plan(hold, HoldClass.TIMEOUT)
        attempt = engine.execute(plan, make_auth(plan), lambda _: {"status": "PASS"})
        self.assertEqual(
            engine.reverify(hold, attempt, verify(attempt, source_sha="1" * 40)),
            HoldDisposition.PROTECTED_HOLD,
        )

    def test_reverification_rejects_wrong_iteration(self):
        engine = RecoveryEngine()
        hold = make_hold()
        plan = engine.recovery_plan(hold, HoldClass.TIMEOUT)
        attempt = engine.execute(plan, make_auth(plan), lambda _: {"status": "PASS"})
        self.assertEqual(
            engine.reverify(hold, attempt, verify(attempt, iteration_id="iteration-999")),
            HoldDisposition.PROTECTED_HOLD,
        )

    def test_reverification_rejects_never_pass_state(self):
        engine = RecoveryEngine()
        hold = make_hold()
        plan = engine.recovery_plan(hold, HoldClass.TIMEOUT)
        attempt = engine.execute(plan, make_auth(plan), lambda _: {"status": "PASS"})
        self.assertEqual(
            engine.reverify(hold, attempt, verify(attempt, state="TIMEOUT")),
            HoldDisposition.PROTECTED_HOLD,
        )

    def test_reverification_conflict_never_releases(self):
        engine = RecoveryEngine()
        hold = make_hold()
        plan = engine.recovery_plan(hold, HoldClass.TIMEOUT)
        attempt = engine.execute(plan, make_auth(plan), lambda _: {"status": "PASS"})
        self.assertEqual(
            engine.reverify(hold, attempt, verify(attempt, conflict=True)),
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
        self.assertEqual(record["plan_fingerprint"], FINGERPRINT)

    def test_execution_limit_is_bounded_and_emits_evidence(self):
        engine = RecoveryEngine(max_execution_steps=2)
        plan = RecoveryPlan(HOLD, ITER, SHA, HoldClass.TIMEOUT, 1, execution_steps=3)
        auth = make_auth(plan)
        with self.assertRaises(RecoveryError):
            engine.execute(plan, auth, lambda _: {"status": "PASS"})
        self.assertEqual(len(engine.rejections), 1)
        self.assertEqual(engine.rejections[0].reason, "execution limit exceeded")

    def test_exhausted_execution_emits_evidence(self):
        engine = RecoveryEngine(max_attempts=1)
        hold = make_hold()
        plan = engine.recovery_plan(hold, HoldClass.TIMEOUT)
        attempt = engine.execute(plan, make_auth(plan), lambda _: {"status": "FAIL"})
        self.assertEqual(attempt.attempt, 1)
        exhausted = engine.recovery_plan(hold, HoldClass.TIMEOUT)
        self.assertEqual(exhausted.classification, HoldClass.EXHAUSTED_ATTEMPTS)
        with self.assertRaises(RecoveryError):
            engine.execute(exhausted, make_auth(exhausted), lambda _: {"status": "PASS"})
        self.assertEqual(engine.rejections[-1].reason, "protected_hold_classification")

    def test_attempt_binding_cannot_be_crossed(self):
        engine = RecoveryEngine()
        hold = make_hold()
        plan = engine.recovery_plan(hold, HoldClass.TIMEOUT)
        attempt = engine.execute(plan, make_auth(plan), lambda _: {"status": "PASS"})
        other = make_hold("hold-002")
        self.assertEqual(
            engine.reverify(other, attempt, verify(attempt, hold_id="hold-002")),
            HoldDisposition.PROTECTED_HOLD,
        )


if __name__ == "__main__":
    unittest.main()
