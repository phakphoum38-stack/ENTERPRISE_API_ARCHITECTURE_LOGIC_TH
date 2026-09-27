from __future__ import annotations
import json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class FinalBaselineContractTests(unittest.TestCase):
    def test_contract_is_active_and_fail_closed(self):
        c=json.loads((ROOT/"current/RESEARCH_OS_PLATFORM_FINAL_BASELINE_CONTRACT.json").read_text(encoding="utf-8"))
        self.assertEqual(c["status"],"ACTIVE")
        for k in ("may_execute","may_authorize","may_merge","may_release"): self.assertFalse(c["authority"][k])
        self.assertEqual(c["authority"]["release_authority"],"FINAL_GATE")
    def test_runtime_matrix_is_complete(self):
        c=json.loads((ROOT/"current/RESEARCH_OS_PLATFORM_FINAL_BASELINE_CONTRACT.json").read_text(encoding="utf-8"))
        self.assertTrue({"normal_execution","retry","duplicate_delivery","idempotency","retry_exhaustion","dlq","replay","worker_crash","restart_recovery","stale_ack","stale_sha","resource_conflict","version_branching","unknown_hold"}.issubset(set(c["runtime_matrix"])))
    def test_invariants_are_fail_closed(self):
        c=json.loads((ROOT/"current/RESEARCH_OS_PLATFORM_FINAL_BASELINE_CONTRACT.json").read_text(encoding="utf-8"))
        self.assertTrue({"unknown_not_pass","deferred_not_pass","resource_conflict_reject_stop_release_ack_reconcile","final_gate_is_single_release_authority"}.issubset(set(c["required_invariants"])))
if __name__=="__main__": unittest.main()
