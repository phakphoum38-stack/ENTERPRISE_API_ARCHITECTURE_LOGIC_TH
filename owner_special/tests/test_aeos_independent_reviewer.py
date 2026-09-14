import unittest

from tools.aeos_independent_reviewer import (
    ACTOR_ID,
    IndependentReviewError,
    ReviewEvidence,
    perform_independent_review,
)

SHA = "a" * 40
HEAD = "b" * 40
BASELINE = "c" * 40


def evidence(**overrides):
    values = dict(
        repository="phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH",
        pull_request=407,
        base_sha=SHA,
        head_sha=HEAD,
        protected_baseline=BASELINE,
        changed_files=("tools/aeos_universal_failure_protocol.py",),
        ci_pass=True,
        forensic_pass=True,
        tests_pass=True,
        provenance_pass=True,
        scope_pass=True,
        authority_boundary_pass=True,
        source_identity_pass=True,
        root_cause_verified=True,
    )
    values.update(overrides)
    return ReviewEvidence(**values)


class IndependentReviewerTests(unittest.TestCase):
    def test_pass_is_review_only_and_recommends_pre_authority(self):
        result = perform_independent_review(evidence())
        self.assertEqual(result.actor, ACTOR_ID)
        self.assertEqual(result.authority, "REVIEW_ONLY")
        self.assertEqual(result.decision, "PASS")
        self.assertEqual(result.recommendation, "PROCEED TO PRE-AUTHORITY")
        self.assertEqual(result.owner_authority, "NOT GRANTED")
        self.assertEqual(result.merge_authorization, "LOCKED")
        self.assertEqual(len(result.evidence_digest), 64)

    def test_any_failed_control_holds(self):
        for field in (
            "ci_pass", "forensic_pass", "tests_pass", "provenance_pass",
            "scope_pass", "authority_boundary_pass", "source_identity_pass",
            "root_cause_verified",
        ):
            with self.subTest(field=field):
                result = perform_independent_review(evidence(**{field: False}))
                self.assertEqual(result.decision, "HOLD")
                self.assertEqual(result.recommendation, "HARD_STOP")
                self.assertIn(field.replace("_pass", "").upper().replace("_", "_"), result.findings)

    def test_invalid_identity_fails_closed(self):
        with self.assertRaises(IndependentReviewError):
            perform_independent_review(evidence(head_sha="not-a-sha"))

    def test_empty_scope_fails_closed(self):
        with self.assertRaises(IndependentReviewError):
            perform_independent_review(evidence(changed_files=()))

    def test_canonical_record_never_grants_authority(self):
        result = perform_independent_review(evidence())
        record = result.canonical()
        self.assertFalse(record.get("approve", False))
        self.assertFalse(record.get("merge", False))
        self.assertEqual(record["owner_authority"], "NOT GRANTED")
        self.assertEqual(record["merge_authorization"], "LOCKED")


if __name__ == "__main__":
    unittest.main()
