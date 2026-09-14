import unittest

from tools.aeos_autobot_horizon_loop import (
    Finding,
    HorizonLoopError,
    LoopState,
    RepairSet,
    build_repair_set,
    run_horizon_loop,
)
from tools.aeos_universal_failure_protocol import (
    FailureRecord,
    UniversalFailureError,
    build_universal_repair_batch,
    collapse_failures,
    completion_ready,
    normalize_failures,
)

SHA = "a" * 40
SHA2 = "b" * 40


def finding(horizon, status="PASS", root=None, fp=None):
    return Finding(horizon=horizon, dimension="integration", status=status,
                   symptom="ok" if status == "PASS" else "failure",
                   fingerprint=fp or (horizon.lower() + "0" * 60), root_cause=root)


def failure(fid, scope, dimension, root, source=SHA, status="FAIL"):
    return FailureRecord(fid, scope, dimension, status, "failure", f"evidence:{fid}", source, root)


class HorizonLoopTests(unittest.TestCase):
    def test_build_repair_set_collapses_duplicate_root_causes(self):
        items = [finding("H00", "FAIL", "same-root"), finding("H01", "FAIL", "same-root")]
        repair = build_repair_set(items, {"same-root": "repair shared defect"},
                                  ["tools/fix.py"], ["owner_special/tests/test_fix.py"])
        self.assertEqual(repair.root_causes, ("same-root",))

    def test_unknown_root_cause_fails_closed(self):
        with self.assertRaises(HorizonLoopError):
            build_repair_set([finding("H00", "FAIL")], {}, ["tools/fix.py"], ["owner_special/tests/test_fix.py"])

    def test_loop_repairs_then_full_rescan_finishes(self):
        calls = []
        def discover(source_sha):
            calls.append(source_sha)
            if source_sha == SHA:
                return [finding(h, "FAIL" if h == "H10" else "PASS", "root" if h == "H10" else None) for h in [f"H{i:02d}" for i in range(28)]]
            return [finding(f"H{i:02d}") for i in range(28)]
        def plan(items):
            return RepairSet(("root",), ("fix",), ("tools/fix.py",), ("owner_special/tests/test_fix.py",), "c" * 64)
        def apply(repair, source_sha):
            self.assertEqual(source_sha, SHA)
            return SHA2
        result = run_horizon_loop(source_sha=SHA, discover=discover, plan_repair=plan,
                                  apply_repair=apply, verify=lambda sha: discover(sha),
                                  independent_verify=lambda sha: sha == SHA2)
        self.assertEqual(result.state, LoopState.FINISHED)
        self.assertEqual(result.source_sha, SHA2)
        self.assertEqual(len(result.repair_sets), 1)
        self.assertGreaterEqual(len(calls), 2)

    def test_missing_horizon_hard_stops(self):
        result = run_horizon_loop(source_sha=SHA, discover=lambda sha: [finding("H00")],
                                  plan_repair=lambda items: (_ for _ in ()).throw(AssertionError("must not repair")),
                                  apply_repair=lambda repair, sha: SHA2, verify=lambda sha: [],
                                  independent_verify=lambda sha: True)
        self.assertEqual(result.state, LoopState.HARD_STOP)
        self.assertEqual(result.hard_stop, "INCOMPLETE_HORIZON")

    def test_unchanged_repair_is_hard_stop(self):
        items = [finding(f"H{i:02d}", "FAIL", "root") if i == 10 else finding(f"H{i:02d}") for i in range(28)]
        result = run_horizon_loop(source_sha=SHA, discover=lambda sha: items,
                                  plan_repair=lambda items: RepairSet(("root",), ("fix",), ("tools/fix.py",), ("owner_special/tests/test_fix.py",), "d" * 64),
                                  apply_repair=lambda repair, sha: sha, verify=lambda sha: items,
                                  independent_verify=lambda sha: False)
        self.assertEqual(result.state, LoopState.HARD_STOP)
        self.assertEqual(result.hard_stop, "REPAIR_DID_NOT_CHANGE_IDENTITY")

    def test_independent_verification_is_required(self):
        result = run_horizon_loop(source_sha=SHA, discover=lambda sha: [finding(f"H{i:02d}") for i in range(28)],
                                  plan_repair=lambda items: (_ for _ in ()).throw(AssertionError("must not repair")),
                                  apply_repair=lambda repair, sha: SHA2, verify=lambda sha: [],
                                  independent_verify=lambda sha: False)
        self.assertEqual(result.state, LoopState.HARD_STOP)
        self.assertEqual(result.hard_stop, "INDEPENDENT_VERIFICATION_FAILED")

    def test_universal_intake_accepts_non_horizon_failures(self):
        records = [failure("F1", "CI", "workflow", "shared-root"), failure("F2", "artifact", "provenance", "shared-root")]
        groups = collapse_failures(records, SHA)
        self.assertEqual(tuple(groups), ("shared-root",))
        self.assertEqual(len(groups["shared-root"]), 2)
        self.assertEqual(build_universal_repair_batch(records, SHA), ("shared-root",))

    def test_universal_intake_rejects_stale_evidence(self):
        with self.assertRaises(UniversalFailureError):
            normalize_failures([failure("F1", "CI", "workflow", "root", source=SHA2)], SHA)

    def test_universal_intake_allows_unknown_root_until_causal_analysis(self):
        records = [failure("F2", "tests", "semantic", None)]
        normalized = normalize_failures(records, SHA)
        self.assertEqual(normalized[0].root_cause, None)
        with self.assertRaises(UniversalFailureError):
            collapse_failures(records, SHA)

    def test_universal_intake_rejects_missing_evidence(self):
        bad_evidence = FailureRecord("F1", "CI", "workflow", "FAIL", "x", "", SHA, "root")
        with self.assertRaises(UniversalFailureError):
            normalize_failures([bad_evidence], SHA)

    def test_universal_completion_requires_all_pass(self):
        passes = [failure("P1", "H00", "tests", None, status="PASS")]
        self.assertTrue(completion_ready(passes, SHA))
        self.assertFalse(completion_ready([failure("F1", "CI", "workflow", "root")], SHA))


if __name__ == "__main__":
    unittest.main()
