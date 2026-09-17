import unittest

from tools.forensics.execution import (
    Finding,
    Observation,
    Outcome,
    bounded_worker_matrix,
    isolate,
    report_json,
)

TARGET = "62ab05d47e1888522b1fe33fff1cf5edefaacea3"
SOURCE = "565ab068d5a1540ea799b594ff031ba003e068af"


class UniversalForensicsTests(unittest.TestCase):
    def obs(self, probe, outcome, workers=None, detail="same"):
        return Observation("research-os", TARGET, SOURCE, probe, outcome, 0 if outcome is not Outcome.UNKNOWN else None, detail, workers)

    def test_concurrency_isolation_is_evidence_based(self):
        report = isolate([
            self.obs("direct", Outcome.PASS),
            self.obs("shell", Outcome.PASS),
            self.obs("platform", Outcome.PASS, 1),
            self.obs("platform", Outcome.FAIL, 4),
        ])
        self.assertEqual(report.finding, Finding.CONCURRENCY_SUSPECTED)
        self.assertEqual(len(report.signatures), 4)

    def test_shell_boundary_isolated_without_concurrency_claim(self):
        report = isolate([
            self.obs("direct", Outcome.PASS),
            self.obs("shell", Outcome.FAIL),
        ])
        self.assertEqual(report.finding, Finding.SHELL_BOUNDARY_SUSPECTED)

    def test_direct_failure_blocks_shortcut(self):
        report = isolate([self.obs("direct", Outcome.FAIL), self.obs("shell", Outcome.PASS)])
        self.assertEqual(report.finding, Finding.RUNTIME_OR_COMMAND_SUSPECTED)

    def test_ambiguous_evidence_holds(self):
        report = isolate([self.obs("direct", Outcome.UNKNOWN), self.obs("shell", Outcome.UNKNOWN)])
        self.assertEqual(report.finding, Finding.HOLD_ISOLATE)

    def test_target_sha_is_exact(self):
        with self.assertRaises(ValueError):
            Observation("p", "not-a-sha", None, "direct", Outcome.FAIL)

    def test_target_must_be_consistent(self):
        other = "a" * 40
        with self.assertRaises(ValueError):
            isolate([self.obs("direct", Outcome.PASS), Observation("p", other, None, "direct", Outcome.PASS)])

    def test_worker_matrix_is_bounded_and_deterministic(self):
        self.assertEqual(bounded_worker_matrix([16, 1, 4, 4]), (1, 4, 16))
        with self.assertRaises(ValueError):
            bounded_worker_matrix([1, 17], maximum=16)

    def test_report_is_deterministic_json(self):
        report = isolate([self.obs("direct", Outcome.PASS)])
        first = report_json(report)
        second = report_json(report)
        self.assertEqual(first, second)
        self.assertIn("universal-forensics-v1", first)


if __name__ == "__main__":
    unittest.main()
