import unittest

from owner_special.research_os_friend.aeos_extended_assurance_checks import (
    CheckObservation,
    CheckState,
    evaluate_check,
)


class AeosExtendedAssuranceCheckTests(unittest.TestCase):
    def _observation(self, state=CheckState.PASS, *, independent=True, fresh=True, value=True):
        return CheckObservation(
            state=state,
            evidence_refs=("evidence:test",),
            independent=independent,
            fresh=fresh,
            details={"dependency_integrity": value},
        )

    def test_missing_evidence_is_rejected(self):
        with self.assertRaises(ValueError):
            CheckObservation(CheckState.PASS, (), True, True, {})

    def test_unknown_stale_conflict_and_blocked_never_pass(self):
        for state in (CheckState.UNKNOWN, CheckState.STALE, CheckState.CONFLICT, CheckState.BLOCKED):
            result = evaluate_check("DEPENDENCY_INTEGRITY", self._observation(state))
            self.assertEqual(result, state)

    def test_missing_independence_or_freshness_blocks_pass(self):
        self.assertEqual(
            evaluate_check("DEPENDENCY_INTEGRITY", self._observation(independent=False)),
            CheckState.BLOCKED,
        )
        self.assertEqual(
            evaluate_check("DEPENDENCY_INTEGRITY", self._observation(fresh=False)),
            CheckState.BLOCKED,
        )

    def test_missing_predicate_is_unknown(self):
        observation = CheckObservation(CheckState.PASS, ("evidence:test",), True, True, {})
        self.assertEqual(evaluate_check("DEPENDENCY_INTEGRITY", observation), CheckState.UNKNOWN)

    def test_false_predicate_fails(self):
        self.assertEqual(
            evaluate_check("DEPENDENCY_INTEGRITY", self._observation(value=False)),
            CheckState.FAIL,
        )

    def test_unknown_check_id_is_unknown(self):
        self.assertEqual(
            evaluate_check("NOT_A_REGISTERED_CHECK", self._observation()),
            CheckState.UNKNOWN,
        )


if __name__ == "__main__":
    unittest.main()
