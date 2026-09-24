import unittest

from tools.platform_production_completion import run_production_completion, validate_production_completion

class PlatformProductionCompletionTests(unittest.TestCase):
    def test_reconciliation_passes(self) -> None:
        self.assertEqual(validate_production_completion(), ())

    def test_summary_is_fail_closed(self) -> None:
        summary = run_production_completion()
        self.assertEqual(summary["status"], "PASS")
        self.assertEqual(summary["release_authority"], "FINAL_GATE")

if __name__ == "__main__":
    unittest.main()
