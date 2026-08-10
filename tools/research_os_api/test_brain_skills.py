import unittest

from brain_skills import (
    ASSISTANT_LEAF_CAPACITY,
    BRAIN,
    MAX_LEAF_CAPACITY,
    AdaptiveHierarchyPolicy,
    BrainSkillsEngine,
)


class BrainSkillsTests(unittest.TestCase):
    def test_capacity_is_six_to_the_sixth_without_eager_activation(self):
        snapshot = BRAIN.capacity_snapshot()
        self.assertEqual(snapshot["branch_factor"], 6)
        self.assertEqual(snapshot["elastic_tiers"], 6)
        self.assertEqual(snapshot["assistant_6x3_capacity"], 6**3)
        self.assertEqual(snapshot["assistant_6x3_capacity"], ASSISTANT_LEAF_CAPACITY)
        self.assertEqual(snapshot["max_leaf_capacity"], 6**6)
        self.assertEqual(snapshot["max_leaf_capacity"], MAX_LEAF_CAPACITY)
        self.assertEqual(snapshot["default_assistant_mode"], "assistant_6x3")
        modes = {item["mode"]: item for item in snapshot["assistant_modes"]}
        self.assertEqual(
            modes["assistant_6x3"]["theoretical_assistants"],
            ASSISTANT_LEAF_CAPACITY,
        )
        self.assertFalse(snapshot["all_workers_started_by_default"])
        self.assertLess(snapshot["max_active_workers"], snapshot["max_leaf_capacity"])

    def test_assistant_six_cubed_mode_is_named_and_bounded(self):
        engine = BrainSkillsEngine(policy=AdaptiveHierarchyPolicy(max_active_workers=36))
        plan = engine.plan("ขอผู้ช่วย 6^3 สำหรับจัดงานโปรเจกต์ใหญ่")
        self.assertEqual(plan["assistant_profile"]["mode"], "assistant_6x3")
        self.assertTrue(plan["assistant_profile"]["requested_by_objective"])
        self.assertEqual(
            plan["assistant_profile"]["theoretical_assistants"],
            ASSISTANT_LEAF_CAPACITY,
        )
        self.assertEqual(plan["hierarchy"]["complexity_level"], 3)
        self.assertEqual(plan["hierarchy"]["requested_workers"], 6**3)
        self.assertEqual(plan["hierarchy"]["active_workers"], 36)
        self.assertTrue(plan["hierarchy"]["backpressure_applied"])
        self.assertEqual(plan["cognition"]["mode"], "assistant_6x3")
        self.assertEqual(plan["cognition"]["candidate_capacity"], 6**3)

    def test_plan_applies_budget_readiness_and_backpressure(self):
        engine = BrainSkillsEngine(policy=AdaptiveHierarchyPolicy(max_active_workers=36))
        plan = engine.plan(
            "research evidence with agent tools",
            complexity_level=6,
            requested_workers=46656,
            budget_workers=12,
            ready_workers=8,
        )
        self.assertEqual(plan["hierarchy"]["active_workers"], 8)
        self.assertTrue(plan["hierarchy"]["backpressure_applied"])
        self.assertIn("knowledge", plan["selected_skills"])
        self.assertIn("coordination", plan["selected_skills"])
        self.assertIn("tool_selection", plan["selected_skills"])
        self.assertFalse(plan["requires_external_api_key"])
        cognition = plan["cognition"]
        self.assertEqual(cognition["mode"], "compound_6x6")
        self.assertEqual(cognition["candidate_capacity"], 6**6)
        self.assertEqual(cognition["hypothesis_branches"], 8)
        self.assertEqual(cognition["critic_passes"], 6)
        self.assertTrue(cognition["evidence_required"])
        self.assertTrue(cognition["web_search_recommended"])
        self.assertTrue(cognition["bounded"])
        self.assertFalse(cognition["hidden_reasoning_exposed"])

    def test_compound_intelligence_stays_bounded_at_large_capacity(self):
        engine = BrainSkillsEngine(policy=AdaptiveHierarchyPolicy(max_active_workers=1296))
        plan = engine.plan(
            "ค้นข้อมูลล่าสุดพร้อมหลักฐาน",
            complexity_level=6,
            requested_workers=46656,
            ready_workers=1296,
        )
        cognition = plan["cognition"]
        self.assertEqual(plan["hierarchy"]["active_workers"], 1296)
        self.assertEqual(cognition["hypothesis_branches"], 36)
        self.assertEqual(cognition["consensus_quorum"], 24)
        self.assertTrue(cognition["web_search_recommended"])

    def test_research_instructions_require_sources_without_exposing_chain_of_thought(self):
        plan = BRAIN.plan("current research evidence", complexity_level=2)
        instructions = BRAIN.research_instructions(plan)
        self.assertIn("Cite sources", instructions)
        self.assertIn("do not reveal private chain-of-thought", instructions)

    def test_catalog_contains_guarded_brain_skills(self):
        catalog = BRAIN.catalog()
        self.assertEqual(catalog["skill_count"], 10)
        by_id = {item["skill_id"]: item for item in catalog["skills"]}
        self.assertTrue(by_id["safety"]["requires_approval_for_writes"])
        self.assertTrue(by_id["learning"]["requires_approval_for_writes"])
        self.assertEqual(by_id["planning"]["provider_mode"], "provider_neutral")

    def test_invalid_capacity_inputs_are_rejected(self):
        policy = AdaptiveHierarchyPolicy(max_active_workers=6)
        with self.assertRaises(ValueError):
            policy.plan(complexity_level=7)
        with self.assertRaises(ValueError):
            policy.plan(requested_workers=46657)
        with self.assertRaises(ValueError):
            policy.plan(budget_workers=0)


if __name__ == "__main__":
    unittest.main()
