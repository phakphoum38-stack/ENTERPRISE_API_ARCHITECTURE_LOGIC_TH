import unittest

from brain_skills import (
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
        self.assertEqual(snapshot["max_leaf_capacity"], 6**6)
        self.assertEqual(snapshot["max_leaf_capacity"], MAX_LEAF_CAPACITY)
        self.assertFalse(snapshot["all_workers_started_by_default"])
        self.assertLess(snapshot["max_active_workers"], snapshot["max_leaf_capacity"])

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
