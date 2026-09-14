import unittest

from tools.aeos_autobot_horizon_loop import (
    Finding,
    HorizonLoopError,
    LoopState,
    RepairSet,
    build_repair_set,
    run_horizon_loop,
)

SHA = "a" * 40
SHA2 = "b" * 40


def finding(horizon, status="PASS", root=None, fp=None):
    return Finding(
        horizon=horizon,
        dimension="integration",
        status=status,
        symptom="ok" if status == "PASS" else "failure",
        fingerprint=fp or (horizon.lower() + "0" * 60),
        root_cause=root,
    )


class HorizonLoopTests(unittest.TestCase):
    def test_build_repair_set_collapses_duplicate_root_causes(self):
        items = [finding("H00", "FAIL", "same-root"), finding("H01", "FAIL", "same-root")]
        repair = build_repair_set(
            items,
            {"same-root": "repair shared defect"},
            ["tools/fix.py"],
            ["owner_special/tests/test_fix.py"],
        )
        self.assertEqual(repair.root_causes, ("same-root",))

    def test_unknown_root_cause_fails_closed(self):
        with self.assertRaises(HorizonLoopError):
            build_repair_set(
                [finding("H00", "FAIL")],
                {},
                ["tools/fix.py"],
                ["owner_special/tests/test_fix.py"],
            )

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

        result = run_horizon_loop(
            source_sha=SHA,
            discover=discover,
            plan_repair=plan,
            apply_repair=apply,
            verify=lambda sha: discover(sha),
            independent_verify=lambda sha: sha == SHA2,
        )
        self.assertEqual(result.state, LoopState.FINISHED)
        self.assertEqual(result.source_sha, SHA2)
        self.assertEqual(len(result.repair_sets), 1)
        self.assertGreaterEqual(len(calls), 2)

    def test_missing_horizon_hard_stops(self):
        result = run_horizon_loop(
            source_sha=SHA,
            discover=lambda sha: [finding("H00")],
            plan_repair=lambda items: (_ for _ in ()).throw(AssertionError("must not repair")),
            apply_repair=lambda repair, sha: SHA2,
            verify=lambda sha: [],
            independent_verify=lambda sha: True,
        )
        self.assertEqual(result.state, LoopState.HARD_STOP)
        self.assertEqual(result.hard_stop, "INCOMPLETE_HORIZON")

    def test_unchanged_repair_is_hard_stop(self):
        items = [finding(f"H{i:02d}", "FAIL", "root") if i == 10 else finding(f"H{i:02d}") for i in range(28)]
        result = run_horizon_loop(
            source_sha=SHA,
            discover=lambda sha: items,
            plan_repair=lambda items: RepairSet(("root",), ("fix",), ("tools/fix.py",), ("owner_special/tests/test_fix.py",), "d" * 64),
            apply_repair=lambda repair, sha: sha,
            verify=lambda sha: items,
            independent_verify=lambda sha: False,
        )
        self.assertEqual(result.state, LoopState.HARD_STOP)
        self.assertEqual(result.hard_stop, "REPAIR_DID_NOT_CHANGE_IDENTITY")

    def test_independent_verification_is_required(self):
        result = run_horizon_loop(
            source_sha=SHA,
            discover=lambda sha: [finding(f"H{i:02d}") for i in range(28)],
            plan_repair=lambda items: (_ for _ in ()).throw(AssertionError("must not repair")),
            apply_repair=lambda repair, sha: SHA2,
            verify=lambda sha: [],
            independent_verify=lambda sha: False,
        )
        self.assertEqual(result.state, LoopState.HARD_STOP)
        self.assertEqual(result.hard_stop, "INDEPENDENT_VERIFICATION_FAILED")


if __name__ == "__main__":
    unittest.main()
