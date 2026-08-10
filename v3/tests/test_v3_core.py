import unittest

from research_os_v3 import (
    ProviderRegistry,
    ScaleTier,
    UnifiedMasterOrchestrator,
    Workload,
    master_contract,
    providers_contract,
)


class V3CleanCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.master = UnifiedMasterOrchestrator()

    def test_adaptive_scale_profiles(self) -> None:
        cases = (
            (Workload(estimated_leaf_tasks=1), ScaleTier.TIER_1_3, 1),
            (Workload(estimated_leaf_tasks=2), ScaleTier.TIER_3_3, 27),
            (Workload(estimated_leaf_tasks=30), ScaleTier.TIER_6_3, 216),
            (Workload(estimated_leaf_tasks=217), ScaleTier.TIER_6_6, 46656),
        )
        for workload, expected_tier, expected_capacity in cases:
            with self.subTest(workload=workload):
                decision = self.master.decide(workload)
                self.assertEqual(decision.profile.tier, expected_tier)
                self.assertEqual(decision.profile.capacity, expected_capacity)

    def test_max_profile_uses_backpressure_when_demand_exceeds_capacity(self) -> None:
        decision = self.master.decide(Workload(estimated_leaf_tasks=50000))
        self.assertEqual(decision.profile.tier, ScaleTier.TIER_6_6)
        self.assertIn("queue/backpressure", decision.reason)

    def test_factory_pipeline_is_deterministic(self) -> None:
        _, plan = self.master.plan(Workload(estimated_leaf_tasks=30))
        self.assertEqual(
            [stage.name for stage in plan.stages],
            ["master", "factory", "team", "tests", "release"],
        )
        self.assertEqual(plan.maximum_leaf_capacity, 216)

    def test_provider_contract_never_exposes_secret(self) -> None:
        payload = providers_contract(ProviderRegistry())
        provider = payload["providers"][0]
        self.assertEqual(provider["name"], "mock")
        self.assertTrue(provider["ready"])
        self.assertFalse(provider["secret_exposed"])
        self.assertNotIn("api_key", provider)
        self.assertNotIn("token", provider)

    def test_master_contract_is_stable(self) -> None:
        decision = self.master.decide(Workload(estimated_leaf_tasks=217))
        payload = master_contract(decision)
        self.assertEqual(payload["contract"], "unified-master-orchestrator-v3-clean")
        self.assertEqual(payload["scale"], "6^6")
        self.assertEqual(payload["maximum_leaf_capacity"], 46656)


if __name__ == "__main__":
    unittest.main()
