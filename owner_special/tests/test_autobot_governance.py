import unittest

from owner_special.research_os_friend.autobot_governance import (
    ActionLedger,
    AutobotAction,
    CircuitBreaker,
    FailureClass,
    GenerationManifest,
    GovernanceError,
    RepairBudget,
    classify_failure,
    retry_allowed,
    validate_capabilities,
    validate_repair_scope,
)


SHA_A = "a" * 40
SHA_B = "b" * 40


class AutobotGovernanceTests(unittest.TestCase):
    def test_generation_manifest_binds_input_and_hashes(self):
        manifest = GenerationManifest(
            generator_id="research-os-generator",
            generator_version="1.0.0",
            input_sha=SHA_A,
            outputs=(("generated.txt", "a" * 64),),
            schema="research-os-generation-manifest/v1",
        )
        self.assertEqual(manifest.input_sha, SHA_A)

    def test_generation_manifest_rejects_duplicate_outputs(self):
        with self.assertRaises(GovernanceError):
            GenerationManifest(
                "generator", "1", SHA_A,
                (("same", "a" * 64), ("same", "b" * 64)),
                "schema/v1",
            )

    def test_action_ledger_is_append_only_and_fingerprinted(self):
        ledger = ActionLedger()
        first = ledger.append(AutobotAction(
            "job-1", "corr-1", SHA_A, 0, "diagnose", "ci failure", "RECORDED"
        ))
        second = ledger.append(AutobotAction(
            "job-1", "corr-1", SHA_A, 1, "repair", "confirmed cause", "SUBMITTED", SHA_B, "123"
        ))
        self.assertNotEqual(first, second)
        self.assertEqual(len(ledger.entries), 2)
        with self.assertRaises(AttributeError):
            ledger.entries.append(None)

    def test_failure_classification_is_conservative(self):
        self.assertEqual(classify_failure("Flutter test failed: assertionerror"), FailureClass.TEST)
        self.assertEqual(classify_failure("sha mismatch for target commit"), FailureClass.IDENTITY)
        self.assertEqual(classify_failure("provenance verification failed"), FailureClass.PROVENANCE)
        self.assertEqual(classify_failure("something strange happened"), FailureClass.UNKNOWN)

    def test_ambiguous_failure_does_not_retry(self):
        budget = RepairBudget(max_attempts=3)
        self.assertFalse(retry_allowed(FailureClass.UNKNOWN, 0, budget))
        self.assertTrue(retry_allowed(FailureClass.INFRASTRUCTURE, 0, budget))
        self.assertFalse(retry_allowed(FailureClass.INFRASTRUCTURE, 3, budget))

    def test_repair_budget_is_bounded(self):
        budget = RepairBudget(max_attempts=2, max_files_per_repair=2)
        self.assertTrue(budget.allows(0, 2))
        self.assertFalse(budget.allows(2, 1))
        self.assertFalse(budget.allows(0, 3))

    def test_circuit_breaker_stops_repeated_failure(self):
        breaker = CircuitBreaker(max_same_failure=2, max_total_attempts=5)
        self.assertFalse(breaker.should_stop(("a",)))
        self.assertTrue(breaker.should_stop(("a", "a")))
        self.assertTrue(breaker.should_stop(("a", "b", "c", "d", "e")))

    def test_capability_boundary_rejects_authority(self):
        allowed = validate_capabilities({"allowed": ["read_repository", "read_ci", "research_web"]})
        self.assertIn("read_ci", allowed)
        with self.assertRaises(GovernanceError):
            validate_capabilities({"allowed": ["release"]})

    def test_repair_scope_rejects_protected_paths(self):
        budget = RepairBudget(max_files_per_repair=4)
        self.assertEqual(validate_repair_scope(("owner_special/foo.py",), budget), ("owner_special/foo.py",))
        with self.assertRaises(GovernanceError):
            validate_repair_scope((".github/workflows/release.yml",), budget)
        with self.assertRaises(GovernanceError):
            validate_repair_scope(("owner_special/research_os_friend/identity_foundation.py",), budget)

    def test_repair_scope_rejects_duplicate_paths(self):
        with self.assertRaises(GovernanceError):
            validate_repair_scope(("a.py", "a.py"), RepairBudget())


if __name__ == "__main__":
    unittest.main()
