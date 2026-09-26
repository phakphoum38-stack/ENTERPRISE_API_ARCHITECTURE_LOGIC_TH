import unittest

from tools.platform_production_completion import run_production_completion, validate_production_completion

class PlatformProductionCompletionTests(unittest.TestCase):
    def test_reconciliation_passes(self) -> None:
        self.assertEqual(validate_production_completion(), ())

    def test_runtime_readiness_is_required_proof(self) -> None:
        from tools.platform_production_completion import ROOT
        import json
        contract = json.loads((ROOT / "current/RESEARCH_OS_PLATFORM_PRODUCTION_COMPLETION_CONTRACT.json").read_text(encoding="utf-8"))
        self.assertTrue(contract["required_proofs"]["runtime_readiness_state_machine"])

    def test_summary_is_fail_closed(self) -> None:
        summary = run_production_completion()
        self.assertEqual(summary["status"], "PASS")
        self.assertEqual(summary["release_authority"], "FINAL_GATE")

if __name__ == "__main__":
    unittest.main()
