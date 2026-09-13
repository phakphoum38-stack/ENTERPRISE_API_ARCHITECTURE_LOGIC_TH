import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("verify_pr_checks.py")
SPEC = spec_from_file_location("verify_pr_checks", MODULE_PATH)
VERIFY_PR_CHECKS = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(VERIFY_PR_CHECKS)

classify = VERIFY_PR_CHECKS.classify
normalize_check_run = VERIFY_PR_CHECKS.normalize_check_run
normalize_status_context = VERIFY_PR_CHECKS.normalize_status_context
poll_interval = VERIFY_PR_CHECKS.poll_interval


class VerifyPrChecksTests(unittest.TestCase):
    def test_self_check_run_is_excluded_by_run_url(self):
        self.assertIsNone(
            normalize_check_run(
                {
                    "name": "comprehensive-review",
                    "status": "in_progress",
                    "details_url": "https://github.com/o/r/actions/runs/123/job/456",
                },
                "123",
            )
        )

    def test_self_check_run_is_excluded_by_plain_run_url(self):
        self.assertIsNone(
            normalize_check_run(
                {
                    "name": "comprehensive-review",
                    "status": "completed",
                    "conclusion": "success",
                    "details_url": "https://github.com/o/r/actions/runs/123",
                },
                "123",
            )
        )

    def test_skipped_check_run_is_treated_as_passing(self):
        check = normalize_check_run(
            {
                "name": "build-ios-unsigned-ipa",
                "status": "completed",
                "conclusion": "skipped",
                "details_url": "https://github.com/o/r/actions/runs/999/job/1",
            },
            "123",
        )
        self.assertEqual(check["bucket"], "pass")
        self.assertEqual(check["state"], "SKIPPED")

    def test_neutral_check_run_is_treated_as_passing(self):
        check = normalize_check_run(
            {
                "name": "non-blocking-note",
                "status": "completed",
                "conclusion": "neutral",
            },
            "123",
        )
        self.assertEqual(check["bucket"], "pass")
        self.assertEqual(check["state"], "NEUTRAL")

    def test_pending_and_failed_checks_are_classified_separately(self):
        pending, bad = classify(
            [
                {
                    "source": "check_run",
                    "name": "ci",
                    "bucket": "pending",
                    "state": "IN_PROGRESS",
                },
                {
                    "source": "status",
                    "name": "lint",
                    "bucket": "fail",
                    "state": "FAILURE",
                },
            ]
        )
        self.assertEqual([item["name"] for item in pending], ["ci"])
        self.assertEqual([item["name"] for item in bad], ["lint"])

    def test_status_context_can_be_excluded_by_run_url(self):
        self.assertIsNone(
            normalize_status_context(
                {
                    "context": "AEOS One-Shot Comprehensive Review",
                    "state": "pending",
                    "target_url": "https://github.com/o/r/actions/runs/123/job/456",
                },
                "123",
            )
        )

    def test_status_context_can_be_excluded_by_plain_run_url(self):
        self.assertIsNone(
            normalize_status_context(
                {
                    "context": "AEOS One-Shot Comprehensive Review",
                    "state": "pending",
                    "target_url": "https://github.com/o/r/actions/runs/123",
                },
                "123",
            )
        )

    def test_poll_interval_backs_off_and_caps(self):
        self.assertEqual(poll_interval(1, 5, 30), 5)
        self.assertEqual(poll_interval(4, 5, 30), 10)
        self.assertEqual(poll_interval(7, 5, 30), 20)
        self.assertEqual(poll_interval(10, 5, 30), 30)


if __name__ == "__main__":
    unittest.main()
