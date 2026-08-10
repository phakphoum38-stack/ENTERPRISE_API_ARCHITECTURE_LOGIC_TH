import tempfile
import unittest
from pathlib import Path

from software_factory.dependency_graph import DependencyGraph
from software_factory.evidence_store import JsonlEvidenceStore
from software_factory.control_plane import EvidenceRecord
from software_factory.provider_router import AgentProviderRouter, ProviderCapability
from software_factory.repair_loop import RetryRepairLoop
from software_factory.scheduler import DynamicResourceScheduler, ResourceBudget


class DependencyGraphTests(unittest.TestCase):
    def test_topological_order_and_ready(self) -> None:
        graph = DependencyGraph()
        graph.add_dependency("v2", "v1")
        graph.add_dependency("v3", "v2")
        self.assertEqual(graph.topological_order(), ("v1", "v2", "v3"))
        self.assertEqual(graph.ready(set()), ("v1",))
        self.assertEqual(graph.ready({"v1"}), ("v2",))

    def test_cycle_is_rejected(self) -> None:
        graph = DependencyGraph()
        graph.add_dependency("v2", "v1")
        with self.assertRaises(ValueError):
            graph.add_dependency("v1", "v2")


class SchedulerTests(unittest.TestCase):
    def test_budget_limits_factory_and_agent_activation(self) -> None:
        scheduler = DynamicResourceScheduler(ResourceBudget(2, 3))
        self.assertEqual(scheduler.admit(("v1", "v2", "v3")), ("v1", "v2"))
        self.assertEqual(scheduler.agent_slots_for("v1", 9), 3)
        scheduler.release("v1")
        self.assertEqual(scheduler.admit(("v3",)), ("v3",))


class ProviderRouterTests(unittest.TestCase):
    def test_capability_first_routing(self) -> None:
        router = AgentProviderRouter()
        router.register(ProviderCapability("provider-a", frozenset({"code", "test"}), priority=20))
        router.register(ProviderCapability("provider-b", frozenset({"code", "test", "vision"}), priority=10))
        self.assertEqual(router.route({"code", "test"}), "provider-b")
        router.disable("provider-b")
        self.assertEqual(router.route({"code"}), "provider-a")


class EvidenceStoreTests(unittest.TestCase):
    def test_jsonl_store_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = JsonlEvidenceStore(Path(directory) / "evidence.jsonl")
            record = EvidenceRecord("2026-01-01T00:00:00+00:00", "v1", "test", "passed")
            store.append(record)
            self.assertEqual(store.read_all(), (record,))


class RepairLoopTests(unittest.TestCase):
    def test_repair_then_success(self) -> None:
        state = {"attempts": 0, "repairs": 0}

        def execute() -> str:
            state["attempts"] += 1
            if state["attempts"] < 2:
                raise RuntimeError("transient")
            return "ok"

        def repair(error: Exception, attempt: int) -> None:
            self.assertIsInstance(error, RuntimeError)
            self.assertEqual(attempt, 1)
            state["repairs"] += 1

        outcome = RetryRepairLoop(max_attempts=3).run(execute, repair)
        self.assertTrue(outcome.success)
        self.assertEqual(outcome.result, "ok")
        self.assertEqual(state["repairs"], 1)


if __name__ == "__main__":
    unittest.main()
