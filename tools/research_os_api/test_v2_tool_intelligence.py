#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from providers import AIProvider, ProviderResult
from v2_brain_core import ActivityLedger
from v2_learning_engine import LearningEngine
from v2_tool_intelligence import TOOL_INTELLIGENCE_CONTRACT, ToolIntelligence
from v2_tool_registry import ToolDefinition, ToolRegistry


class FakeSearchProvider(AIProvider):
    name = "fake-search"

    def generate(self, prompt: str, *, system: str = "", model: str | None = None) -> ProviderResult:
        del prompt, system
        return ProviderResult(self.name, model or "fake-v1", "ok", {"fake": True})

    def search(self, query: str, *, system: str = "", model: str | None = None) -> ProviderResult:
        del query, system
        payload = {
            "candidates": [
                {
                    "name": "Example Tool",
                    "url": "https://example.com/tool",
                    "publisher": "Example Publisher",
                    "tool_type": "api",
                    "capabilities": ["web_search", "api_integration"],
                    "integration_modes": ["REST API"],
                    "platforms": ["Windows", "Linux", "macOS"],
                    "license": "Apache-2.0",
                    "requires_credentials": True,
                    "network_required": True,
                    "evidence_urls": [
                        "https://example.com/docs",
                        "https://example.com/security",
                    ],
                    "risk_level": "low",
                    "recommendation": "Evaluate with a read-only adapter first.",
                }
            ]
        }
        return ProviderResult(
            self.name,
            model or "fake-search-v1",
            json.dumps(payload),
            {"fake": True},
            ({"url": "https://example.com/docs", "title": "Docs"},),
        )


class ToolIntelligenceTests(unittest.TestCase):
    def make_intelligence(self, root: str) -> ToolIntelligence:
        registry = ToolRegistry(tools=())
        registry.register(
            ToolDefinition(
                "test.web.inspect",
                "1.0.0",
                "Read-only Web Inspector",
                "Read-only web inspection tool.",
                ("web_search",),
                permissions=("runtime.read",),
                network=True,
                mutating=False,
                destructive=False,
                secret_access=False,
                supports_dry_run=True,
            )
        )
        registry.register_adapter(
            "test.web.inspect",
            lambda action, payload, dry_run: {
                "action": action,
                "payload": dict(payload),
                "dry_run": dry_run,
            },
        )
        learning = LearningEngine(ActivityLedger(Path(root)))
        return ToolIntelligence(
            registry,
            learning,
            search_provider_factory=lambda name: FakeSearchProvider(),
        )

    def test_rank_existing_prefers_ready_minimum_risk_tool(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            intelligence = self.make_intelligence(tmp)
            result = intelligence.rank_existing(["web_search"])
        self.assertEqual(result["contract"], TOOL_INTELLIGENCE_CONTRACT)
        self.assertEqual(result["selected_tool_id"], "test.web.inspect")
        self.assertEqual(result["missing_capabilities"], [])
        self.assertTrue(result["ranked"][0]["ready"])
        self.assertFalse(result["selection_executes_tool"])

    def test_plan_identifies_capability_gaps_without_installing_anything(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            intelligence = self.make_intelligence(tmp)
            result = intelligence.plan_for_objective(
                "วางแผนระบบฐานข้อมูลและ API",
                context={"required_tool_capabilities": ["database", "api_integration"]},
            )
        self.assertTrue(result["needs_external_discovery"])
        self.assertIn("database", result["existing"]["missing_capabilities"])
        self.assertFalse(result["execution_performed"])
        self.assertFalse(result["discovery_plan"]["automatic_install"])
        self.assertTrue(result["discovery_plan"]["review_required"])

    def test_global_discovery_returns_evidence_backed_candidates_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            intelligence = self.make_intelligence(tmp)
            result = intelligence.discover(
                "ค้นหาเครื่องมือสำหรับ web search และ API",
                capabilities=("web_search", "api_integration"),
            )
        self.assertTrue(result["provider_ready"])
        self.assertEqual(len(result["candidates"]), 1)
        candidate = result["candidates"][0]
        self.assertEqual(candidate["name"], "Example Tool")
        self.assertGreaterEqual(candidate["trust_score"], 70)
        self.assertTrue(candidate["evidence_urls"])
        self.assertFalse(result["automatic_download"])
        self.assertFalse(result["automatic_install"])
        self.assertFalse(result["automatic_execution"])
        self.assertTrue(result["review_required"])

    def test_adapter_design_is_plan_only_and_uses_minimum_permission_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            intelligence = self.make_intelligence(tmp)
            plan = intelligence.design_adapter(
                {
                    "name": "Example Tool",
                    "url": "https://example.com/tool",
                    "capabilities": ["api_integration"],
                    "integration_modes": ["REST API"],
                    "requires_credentials": True,
                    "network_required": True,
                }
            )
        adapter = plan["adapter_plan"]
        self.assertTrue(adapter["reuse_first"])
        self.assertTrue(adapter["credential_boundary_required"])
        self.assertFalse(adapter["automatic_code_generation"])
        self.assertFalse(adapter["automatic_registration"])
        self.assertFalse(adapter["automatic_installation"])
        self.assertFalse(adapter["automatic_execution"])
        self.assertTrue(adapter["review_required"])

    def test_tool_playbook_learns_from_structured_outcomes_not_hidden_reasoning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            intelligence = self.make_intelligence(tmp)
            intelligence.learning.record_experience(
                session_id="tool-training",
                task_id="tool-training-1",
                status="verified",
                objective="verify existing web tool",
                capabilities=("web_search",),
                tool_ids=("test.web.inspect",),
            )
            playbook = intelligence.tool_playbook("test.web.inspect")
        self.assertEqual(playbook["observed_outcomes"]["verified"], 1)
        self.assertIn(playbook["usage_confidence"], {"unproven", "mixed", "established"})
        self.assertFalse(playbook["hidden_reasoning_used"])

    def test_restricted_discovery_category_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            intelligence = self.make_intelligence(tmp)
            with self.assertRaisesRegex(ValueError, "restricted category"):
                intelligence.discover("find gambling tools")


if __name__ == "__main__":
    unittest.main()
