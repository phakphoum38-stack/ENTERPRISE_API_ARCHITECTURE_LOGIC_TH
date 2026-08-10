import json
import tempfile
import unittest
from pathlib import Path

from research_os_v3 import UnifiedMasterOrchestrator, Workload


def handlers(call_order: list[str], *, fail_stage: str | None = None):
    def build(name: str):
        def run(context):
            call_order.append(name)
            if name == fail_stage:
                raise RuntimeError(f"{name} failed")
            if name == "master":
                return {
                    "contract": context.decision.profile.tier.value,
                    "provider": context.decision.provider,
                }
            if name == "factory":
                return {"stages": [stage.name for stage in context.plan.stages]}
            if name == "team":
                return {
                    "active_workers": context.active_workers,
                    "queued_tasks": context.queued_tasks,
                }
            if name == "tests":
                return {"passed": True}
            return {"artifact": "research-os-v3-candidate"}

        return run

    return {
        name: build(name)
        for name in ("master", "factory", "team", "tests", "release")
    }


class FactoryExecutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.master = UnifiedMasterOrchestrator()

    def test_execution_is_bounded_and_does_not_pre_spawn_logical_capacity(self) -> None:
        workload = Workload(estimated_leaf_tasks=217, parallelism=1000)
        result = self.master.execute_factory(
            workload,
            handlers=handlers([]),
            hard_concurrency_limit=64,
            release_inputs={"source_sha": "abc123"},
        )

        self.assertTrue(result.passed)
        self.assertEqual(result.logical_capacity, 46656)
        self.assertEqual(result.active_workers, 64)
        self.assertLess(result.active_workers, result.logical_capacity)
        self.assertGreater(result.queued_tasks, 0)

    def test_execution_order_and_release_manifest_are_reproducible(self) -> None:
        workload = Workload(estimated_leaf_tasks=30, parallelism=6)
        first_order: list[str] = []
        second_order: list[str] = []
        first = self.master.execute_factory(
            workload,
            handlers=handlers(first_order),
            release_inputs={"source_sha": "same-sha", "build_policy": "clean"},
        )
        second = self.master.execute_factory(
            workload,
            handlers=handlers(second_order),
            release_inputs={"build_policy": "clean", "source_sha": "same-sha"},
        )

        expected = ["master", "factory", "team", "tests", "release"]
        self.assertEqual(first_order, expected)
        self.assertEqual(second_order, expected)
        self.assertTrue(first.passed)
        self.assertTrue(second.passed)
        self.assertEqual(first.execution_id, second.execution_id)
        self.assertEqual(
            first.release_manifest["release_sha256"],
            second.release_manifest["release_sha256"],
        )

    def test_failure_preserves_prior_stage_evidence_and_blocks_release(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence_path = Path(temporary) / "execution.json"
            call_order: list[str] = []
            result = self.master.execute_factory(
                Workload(estimated_leaf_tasks=30, parallelism=6),
                handlers=handlers(call_order, fail_stage="team"),
                evidence_path=evidence_path,
                release_inputs={"source_sha": "failure-case"},
            )

            self.assertFalse(result.passed)
            self.assertIsNone(result.release_manifest)
            self.assertEqual(call_order, ["master", "factory", "team"])

            payload = json.loads(evidence_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "failed")
            self.assertEqual(payload["stages"]["master"]["status"], "passed")
            self.assertEqual(payload["stages"]["factory"]["status"], "passed")
            self.assertEqual(payload["stages"]["team"]["status"], "failed")
            self.assertNotIn("tests", payload["stages"])
            self.assertNotIn("release", payload["stages"])
            self.assertNotIn("release_manifest", payload)

    def test_missing_required_stage_handler_fails_closed(self) -> None:
        call_order: list[str] = []
        stage_handlers = handlers(call_order)
        stage_handlers.pop("tests")

        result = self.master.execute_factory(
            Workload(estimated_leaf_tasks=2),
            handlers=stage_handlers,
        )

        self.assertFalse(result.passed)
        self.assertEqual(result.stages[-1].name, "tests")
        self.assertEqual(result.stages[-1].error_type, "MissingStageHandler")
        self.assertIsNone(result.release_manifest)


if __name__ == "__main__":
    unittest.main()
