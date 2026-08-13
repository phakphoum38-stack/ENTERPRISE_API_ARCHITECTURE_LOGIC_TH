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
            self.assertEqual(analysis["result"]["summary"], "inspect evidence")
            gate = self.master.execute_skill("quality-gate", arguments={"checks": {"tests": True}}, context=context)
            self.assertTrue(gate["result"]["passed"])
            bridge = self.master.execute_skill("v3-bridge", context=context)
            self.assertFalse(bridge["result"]["legacy_master_started"])

    def test_owner_friend_native_skills_have_distinct_runtime_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            memories: list[dict[str, object]] = []

            def memory_add(value: str, tags: tuple[str, ...]) -> dict[str, object]:
                item = {"text": value, "tags": list(tags)}
                memories.append(item)
                return item

            def memory_search(query: str, limit: int) -> list[dict[str, object]]:
                wanted = query.lower()
                return [item for item in memories if wanted in str(item["text"]).lower()][:limit]

            def factory_plan(tasks: int) -> dict[str, object]:
                return {"tasks": tasks, "bounded": True}

            context = SkillRuntimeContext(
                user_id="owner",
                profile_id="default",
                user_data_root=Path(temporary),
                repository_root=Path(__file__).resolve().parents[2],
                approved=True,
                memory_search=memory_search,
                memory_add=memory_add,
                factory_plan=factory_plan,
            )

            analysis = self.master.execute_skill("analysis", "inspect constraints?", arguments={"constraints": ["one-master"]}, context=context)
            self.assertEqual(analysis["result"]["constraints"], ["one-master"])
            self.assertGreater(analysis["result"]["words"], 0)

            planning = self.master.execute_skill("planning", arguments={"goal": "ship V3", "tasks": 6}, context=context)
            self.assertEqual(planning["result"]["factory"]["tasks"], 6)
            self.assertIn("validate", planning["result"]["steps"])

            coding = self.master.execute_skill("coding", "UnifiedMasterOrchestrator", context=context)
            self.assertFalse(coding["result"]["mutation_performed"])
            self.assertEqual(coding["result"]["write_boundary"], "governed-tool-execution")

            research = self.master.execute_skill("research", "UnifiedMasterOrchestrator", context=context)
            self.assertTrue(research["result"]["provenance"])
            self.assertGreaterEqual(research["result"]["source_count"], 0)

            data = self.master.execute_skill("data", arguments={"rows": [{"value": 1}, {"value": 2, "label": "ok"}]}, context=context)
            self.assertEqual(data["result"]["row_count"], 2)
            self.assertEqual(data["result"]["numeric_sums"]["value"], 3.0)

            documents = self.master.execute_skill("documents", "evidence body", arguments={"title": "Evidence"}, context=context)
            self.assertTrue(documents["result"]["markdown"].startswith("# Evidence"))
            self.assertFalse(documents["result"]["persisted"])

            automation = self.master.execute_skill("automation", "run quality gate", arguments={"action": "register", "schedule": "manual", "automation_id": "owner-quality"}, context=context)
            self.assertEqual(automation["result"]["status"], "registered")
            self.assertTrue((Path(temporary) / "automation" / "owner-quality.json").is_file())

            added = self.master.execute_skill("memory", "native memory", arguments={"action": "add", "tags": ["v3"]}, context=context)
            self.assertEqual(added["result"]["memory"]["text"], "native memory")
            recalled = self.master.execute_skill("memory", arguments={"action": "search", "query": "native"}, context=context)
            self.assertEqual(len(recalled["result"]["hits"]), 1)

            security = self.master.execute_skill("security", arguments={"write": True, "api_key": "not-read"}, context=context)
            self.assertTrue(security["result"]["write_allowed"])
            self.assertEqual(security["result"]["secret_fields_detected"], ["api_key"])
            self.assertFalse(security["result"]["credential_access"])

            quality = self.master.execute_skill("quality", arguments={"checks": {"tests": True, "evidence": True}}, context=context)
            self.assertTrue(quality["result"]["passed"])
            self.assertTrue(quality["result"]["evidence_required"])

            executed = {analysis["skill"], planning["skill"], coding["skill"], research["skill"], data["skill"], documents["skill"], automation["skill"], added["skill"], security["skill"], quality["skill"]}
            self.assertEqual(executed, {"analysis", "planning", "coding", "research", "data", "documents", "automation", "memory", "security", "quality"})

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
