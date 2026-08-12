import json
import tempfile
import unittest
from pathlib import Path

from research_os_v3 import (
    CompletionRequest,
    DataLayout,
    OpenAICompatibleProvider,
    ProviderRegistry,
    ScaleTier,
    SkillOrigin,
    UnifiedMasterOrchestrator,
    UnifiedSkillRegistry,
    V3LocalService,
    Workload,
    master_contract,
    providers_contract,
)


class StaticSecretSource:
    def __init__(self, values: dict[str, str]) -> None:
        self.values = values

    def get(self, name: str) -> str | None:
        return self.values.get(name)


class FakeTransport:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def post_json(
        self,
        url: str,
        *,
        headers: dict[str, str],
        payload: dict[str, object],
        timeout: float,
    ) -> dict[str, object]:
        self.calls.append(
            {"url": url, "headers": headers, "payload": payload, "timeout": timeout}
        )
        return {"choices": [{"message": {"content": "provider-ok"}}]}


class V3CleanCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.master = UnifiedMasterOrchestrator()

    def test_adaptive_scale_profiles(self) -> None:
        cases = (
            (Workload(estimated_leaf_tasks=1), ScaleTier.TIER_3_1, 3),
            (Workload(estimated_leaf_tasks=4), ScaleTier.TIER_3_3, 27),
            (Workload(estimated_leaf_tasks=30), ScaleTier.TIER_6_3, 216),
            (Workload(estimated_leaf_tasks=217), ScaleTier.TIER_3_6, 729),
            (Workload(estimated_leaf_tasks=730), ScaleTier.TIER_6_6, 46656),
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

    def test_unified_skill_registry_contains_v1_v2_v3_native_skills(self) -> None:
        registry = UnifiedSkillRegistry()
        self.assertEqual(registry.origins(), (SkillOrigin.V1, SkillOrigin.V2, SkillOrigin.V3))
        self.assertTrue(registry.by_origin(SkillOrigin.V1))
        self.assertTrue(registry.by_origin(SkillOrigin.V2))
        self.assertTrue(registry.by_origin(SkillOrigin.V3))
        self.assertTrue(all(skill.native_v3 for skill in registry.list()))
        self.assertIsNotNone(registry.get("adaptive-hierarchy"))
        self.assertIs(self.master.skills.get("adaptive-hierarchy").origin, SkillOrigin.V3)

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

    def test_openai_compatible_provider_uses_secret_without_exposing_it(self) -> None:
        secret = "candidate-provider-secret"
        transport = FakeTransport()
        provider = OpenAICompatibleProvider(
            base_url="https://provider.example/v1",
            model="example-model",
            secret_source=StaticSecretSource({"OPENAI_API_KEY": secret}),
            transport=transport,
            timeout=5.0,
        )

        before = provider.status()
        self.assertTrue(before.ready)
        self.assertFalse(before.connected)
        safe_status = before.to_safe_dict()
        self.assertNotIn(secret, json.dumps(safe_status, sort_keys=True))
        self.assertEqual(safe_status["metadata"]["credential_source"], "OPENAI_API_KEY")

        response = provider.complete(CompletionRequest(prompt="hello"))
        self.assertEqual(response.text, "provider-ok")
        self.assertEqual(response.provider, "openai-compatible")
        self.assertEqual(len(transport.calls), 1)
        call = transport.calls[0]
        self.assertEqual(call["url"], "https://provider.example/v1/chat/completions")
        self.assertEqual(call["headers"]["Authorization"], f"Bearer {secret}")
        self.assertEqual(call["payload"]["model"], "example-model")
        self.assertTrue(provider.status().connected)
        self.assertNotIn(secret, json.dumps(provider.status().to_safe_dict(), sort_keys=True))

    def test_openai_compatible_provider_requires_credential(self) -> None:
        provider = OpenAICompatibleProvider(
            secret_source=StaticSecretSource({}),
            transport=FakeTransport(),
        )
        self.assertFalse(provider.status().ready)
        with self.assertRaisesRegex(RuntimeError, "missing provider credential"):
            provider.complete(CompletionRequest(prompt="hello"))

    def test_local_service_rejects_non_loopback_binding(self) -> None:
        with self.assertRaisesRegex(ValueError, "must bind to a loopback address"):
            V3LocalService(host="0.0.0.0", port=0)

    def test_data_layout_is_idempotent_and_preserves_existing_data(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            layout = DataLayout(Path(temporary)).ensure()
            marker = layout.sessions / "existing.txt"
            marker.write_text("keep", encoding="utf-8")

            second = DataLayout(Path(temporary)).ensure()
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")
            self.assertEqual(
                set(second.directories()),
                {"sessions", "database", "artifacts", "logs", "evidence"},
            )
            self.assertTrue(all(path.is_dir() for path in second.directories().values()))

    def test_master_contract_is_stable(self) -> None:
        decision = self.master.decide(Workload(estimated_leaf_tasks=730))
        payload = master_contract(decision)
        self.assertEqual(payload["contract"], "unified-master-orchestrator-v3-clean")
        self.assertEqual(payload["scale"], "6^6")
        self.assertEqual(payload["maximum_leaf_capacity"], 46656)


if __name__ == "__main__":
    unittest.main()
