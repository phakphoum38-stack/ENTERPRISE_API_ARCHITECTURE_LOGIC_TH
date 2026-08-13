import tempfile
import unittest
from pathlib import Path

from research_os_v3 import (
    DataLayout,
    MemoryStore,
    ScaleTier,
    SkillOrigin,
    SkillRuntimeContext,
    UnifiedMasterOrchestrator,
    UnifiedSkillRegistry,
    UserContext,
    Workload,
    health_contract,
    master_contract,
)


class V3CleanCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.master = UnifiedMasterOrchestrator()

    def test_scale_profiles_and_ceiling(self) -> None:
        cases = ((1, ScaleTier.TIER_3_1, 3), (4, ScaleTier.TIER_3_3, 27), (30, ScaleTier.TIER_6_3, 216), (217, ScaleTier.TIER_3_6, 729), (730, ScaleTier.TIER_6_6, 46656), (46657, ScaleTier.TIER_10_10, 10_000_000_000))
        for tasks, tier, capacity in cases:
            decision = self.master.decide(Workload(estimated_leaf_tasks=tasks))
            self.assertEqual(decision.profile.tier, tier)
            self.assertEqual(decision.profile.capacity, capacity)
        overloaded = self.master.decide(Workload(estimated_leaf_tasks=10_000_000_001))
        self.assertIn("queue/backpressure", overloaded.reason)
        self.assertEqual(health_contract()["capacity_policy"], "lazy-bounded-execution")

    def test_unified_registry_is_fully_native(self) -> None:
        registry = UnifiedSkillRegistry()
        self.assertEqual(registry.origins(), (SkillOrigin.V1, SkillOrigin.V2, SkillOrigin.V3, SkillOrigin.OWNER_FRIEND, SkillOrigin.LEGACY))
        self.assertEqual(len(registry.list()), 40)
        self.assertTrue(all(item.native_v3 and item.runtime_mode == "native" for item in registry.list()))
        self.assertEqual(len(self.master.skill_runtime.handler_names()), 40)
        self.assertEqual(registry.get("coding").execution_adapter, "v3-adapter")
        self.assertEqual(registry.get("chat-runtime").execution_adapter, "v3-core")
        self.assertNotIn("context-adapter", registry.conversation_context())

    def test_migrated_handlers_run_under_one_master(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context = SkillRuntimeContext(user_id="owner", profile_id="default", user_data_root=Path(temporary), repository_root=Path(__file__).resolve().parents[2], approved=True)
            analysis = self.master.execute_skill("analysis", "inspect evidence", context=context)
            self.assertEqual(analysis["result"]["text"], "analysis: inspect evidence")
            gate = self.master.execute_skill("quality-gate", arguments={"checks": {"tests": True}}, context=context)
            self.assertTrue(gate["result"]["passed"])
            bridge = self.master.execute_skill("v3-bridge", context=context)
            self.assertFalse(bridge["result"]["legacy_master_started"])

    def test_memory_agents_tools_and_factory_remain_governed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = MemoryStore(DataLayout(Path(temporary)).ensure())
            alice = UserContext(user_id="alice", profile_id="default")
            bob = UserContext(user_id="bob", profile_id="default")
            store.add(alice, "governed native memory")
            store.add(bob, "other profile data")
            self.assertEqual(len(store.search(alice, "native")), 1)
            self.assertEqual(store.search(alice, "other"), [])
        self.assertEqual(len(self.master.agents.list()), 5)
        self.assertEqual(self.master.execute_tool("echo", {"text": "ok"})["text"], "ok")
        with self.assertRaises(PermissionError):
            self.master.execute_tool("artifact-note", {"text": "blocked"})
        _, plan = self.master.plan(Workload(estimated_leaf_tasks=30))
        self.assertEqual([stage.name for stage in plan.stages], ["master", "factory", "team", "tests", "release"])
        payload = master_contract(self.master.decide(Workload(estimated_leaf_tasks=730)))
        self.assertEqual(payload["system_maximum_logical_capacity"], 10_000_000_000)


if __name__ == "__main__":
    unittest.main()
