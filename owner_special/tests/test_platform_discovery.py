import json
import unittest
from pathlib import Path

from tools.platform_discovery import (
    Backpressure,
    DiscoveryBudget,
    DiscoveryCandidate,
    DiscoveryEngine,
    DiscoveryNode,
    DiscoveryResult,
    build_nodes_from_platform_registry,
)


class Clock:
    def __init__(self, step: float = 0.0):
        self.value = 0.0
        self.step = step

    def __call__(self) -> float:
        current = self.value
        self.value += self.step
        return current


def nodes():
    return [
        DiscoveryNode("root", 0, "PLATFORM", "VIRTUAL_SPACE", root_id="root"),
        DiscoveryNode("a", 1, "INTEGRATION", "WORKSPACE_LEVEL", parent_id="root", root_id="root"),
        DiscoveryNode(
            "target-a", 2, "API Integration", "WORK",
            parent_id="a", root_id="root", capability="compose APIs",
            references=("current/api.json",),
        ),
        DiscoveryNode(
            "target-b", 2, "Other Work", "WORK",
            parent_id="a", root_id="root", capability="other capability",
            references=("current/other.json",),
        ),
    ]


class BoundedDiscoveryTests(unittest.TestCase):
    def test_root_is_required(self):
        engine = DiscoveryEngine(nodes())
        response = engine.discover(virtual_space="PLATFORM", root_id=None, target="API Integration")
        self.assertEqual(response.result, DiscoveryResult.ROOT_UNRESOLVED)
        self.assertFalse(engine.can_create(response))

    def test_same_level_is_checked_before_descending(self):
        engine = DiscoveryEngine(nodes())
        response = engine.discover(
            virtual_space="PLATFORM", root_id="root", target="API Integration"
        )
        self.assertEqual(response.result, DiscoveryResult.FOUND_AT)
        self.assertEqual(response.node_id, "target-a")
        self.assertIn(2, response.proof.levels_examined)

    def test_absent_scope_is_only_createable_state(self):
        engine = DiscoveryEngine(nodes())
        response = engine.discover(virtual_space="PLATFORM", root_id="root", target="does-not-exist")
        self.assertEqual(response.result, DiscoveryResult.ABSENT_FROM_SCOPE)
        self.assertTrue(engine.can_create(response))
        self.assertEqual(response.proof.result, DiscoveryResult.ABSENT_FROM_SCOPE)

    def test_ambiguous_same_level_stops(self):
        data = nodes() + [
            DiscoveryNode(
                "target-c", 2, "API Integration", "WORK",
                parent_id="a", root_id="root", capability="compose APIs",
            )
        ]
        engine = DiscoveryEngine(data)
        response = engine.discover(virtual_space="PLATFORM", root_id="root", target="API Integration")
        self.assertEqual(response.result, DiscoveryResult.AMBIGUOUS)
        self.assertFalse(engine.can_create(response))

    def test_timeout_returns_proof(self):
        clock = Clock(step=0.1)
        budget = DiscoveryBudget(max_time_ms=50, max_depth=4, max_nodes=100)
        engine = DiscoveryEngine(nodes(), budget=budget, clock=clock)
        response = engine.discover(virtual_space="PLATFORM", root_id="root", target="missing")
        self.assertEqual(response.result, DiscoveryResult.TIMEOUT)
        self.assertIn("budget", response.proof.reason)
        self.assertFalse(engine.can_create(response))

    def test_positive_and_negative_cache(self):
        engine = DiscoveryEngine(nodes())
        first = engine.discover(virtual_space="PLATFORM", root_id="root", target="API Integration")
        second = engine.discover(virtual_space="PLATFORM", root_id="root", target="API Integration")
        self.assertEqual(first.node_id, second.node_id)
        self.assertTrue(second.proof.cache_hit)

        absent1 = engine.discover(virtual_space="PLATFORM", root_id="root", target="missing")
        absent2 = engine.discover(virtual_space="PLATFORM", root_id="root", target="missing")
        self.assertEqual(absent1.result, DiscoveryResult.ABSENT_FROM_SCOPE)
        self.assertEqual(absent2.result, DiscoveryResult.ABSENT_FROM_SCOPE)
        self.assertEqual(absent1.proof.discovery_id, absent2.proof.discovery_id)

    def test_capability_duplicates_and_fingerprints(self):
        duplicate = DiscoveryNode(
            "duplicate", 2, "Duplicate", "WORK",
            parent_id="a", root_id="root", capability="compose APIs",
            fingerprint="same",
        )
        first = nodes()[2]
        first = DiscoveryNode(**{**first.__dict__, "fingerprint": "same"})
        engine = DiscoveryEngine(nodes()[:2] + [first, duplicate])
        self.assertEqual(engine.duplicate_capabilities("compose APIs"), [("duplicate", "target-a")])
        self.assertEqual(engine.duplicate_fingerprints("same"), ("duplicate", "target-a"))

    def test_stale_candidates_are_reported_not_deleted(self):
        stale = DiscoveryNode("stale", 2, "Stale", "WORK", parent_id="a", root_id="root")
        engine = DiscoveryEngine(nodes() + [stale])
        self.assertIn("stale", engine.stale_candidates())
        self.assertIn("stale", {n.node_id for n in engine.index.nodes()})

    def test_backpressure_is_fail_closed(self):
        gate = Backpressure(1)
        self.assertTrue(gate.acquire())
        self.assertFalse(gate.acquire())
        gate.release()
        self.assertTrue(gate.acquire())
        gate.release()

    def test_parallel_probe_returns_ranked_results(self):
        engine = DiscoveryEngine(nodes(), budget=DiscoveryBudget(max_workers=2))
        result = engine.same_level_parallel_probe(
            nodes()[2:],
            lambda n: DiscoveryCandidate(n.node_id, n.level, 1.0 if n.name == "API Integration" else 0.5),
        )
        self.assertEqual([x.node_id for x in result], ["target-a", "target-b"])

    def test_emergency_stop_is_fail_closed(self):
        engine = DiscoveryEngine(nodes())
        engine.emergency_stop("test_stop")
        response = engine.discover(virtual_space="PLATFORM", root_id="root", target="API Integration")
        self.assertEqual(response.result, DiscoveryResult.EMERGENCY_STOP)
        self.assertFalse(engine.can_create(response))
        self.assertEqual(response.proof.reason, "test_stop")

    def test_registry_adapter_reuses_existing_virtual_workspace(self):
        root = Path(__file__).resolve().parents[2]
        registry = json.loads(
            (root / "current/PLATFORM_VIRTUAL_WORKSPACE_REGISTRY.json").read_text(encoding="utf-8")
        )
        adapted = build_nodes_from_platform_registry(registry)
        self.assertEqual(adapted[0].node_id, "platform-root")
        self.assertEqual(adapted[0].kind, "VIRTUAL_SPACE")
        work_ids = {x["work_id"] for x in registry["records"]}
        self.assertTrue(work_ids.issubset({n.node_id for n in adapted}))


if __name__ == "__main__":
    unittest.main()
