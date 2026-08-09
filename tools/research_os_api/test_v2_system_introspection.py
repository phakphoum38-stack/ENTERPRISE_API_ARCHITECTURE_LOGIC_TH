#!/usr/bin/env python3
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_platform import AgentRegistry
from v2_brain_core import ActivityLedger, WorkingMemory
from v2_brain_runtime import BrainRuntime
from v2_system_introspection import (
    SYSTEM_INTROSPECTION_CONTRACT,
    SystemIntrospection,
)


class SystemIntrospectionPhase7Tests(unittest.TestCase):
    def make_system(self, root: str) -> SystemIntrospection:
        data = Path(root) / ".runtime"
        data.mkdir()
        runtime = BrainRuntime(
            registry=AgentRegistry(),
            working_memory=WorkingMemory(data),
            ledger=ActivityLedger(data),
        )
        return SystemIntrospection(runtime, AgentRegistry())

    def test_manifest_is_read_only_and_names_existing_sources_of_truth(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            system = self.make_system(tmp)
            manifest = system.manifest()
            self.assertEqual(SYSTEM_INTROSPECTION_CONTRACT, manifest["contract"])
            self.assertTrue(manifest["read_only"])
            self.assertFalse(manifest["execution_authority"])
            self.assertFalse(manifest["hidden_chain_of_thought_exposed"])
            self.assertEqual("agent_platform.REGISTRY", manifest["sources_of_truth"]["operational_agents"])
            self.assertEqual("BrainRuntime.skills", manifest["sources_of_truth"]["skills"])
            self.assertFalse(manifest["safety"]["introspection_grants_permissions"])
            self.assertFalse(manifest["safety"]["production_release_bypass"])

    def test_agent_views_separate_operational_agents_from_brain_team(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            system = self.make_system(tmp)
            all_agents = system.agents()
            operational_ids = {item["agent_id"] for item in all_agents["operational_agents"]}
            brain_ids = {item["agent_id"] for item in all_agents["brain_team"]}
            self.assertIn("developer", operational_ids)
            self.assertIn("v2_brain_reviewer", brain_ids)
            self.assertNotIn("v2_brain_reviewer", operational_ids)

            filtered = system.agents(scope="brain", capability="security_review")
            self.assertEqual(["v2_brain_reviewer"], [item["agent_id"] for item in filtered["brain_team"]])
            self.assertEqual([], filtered["operational_agents"])

    def test_capability_catalog_reports_known_routable_skill_and_executable_states(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            system = self.make_system(tmp)
            payload = system.capabilities()
            by_capability = {item["capability"]: item for item in payload["capabilities"]}
            self.assertIn("skill_registry", by_capability)
            self.assertTrue(by_capability["skill_registry"]["routable"])
            self.assertTrue(by_capability["skill_registry"]["executable"])
            self.assertIn("brain.skills.inspect", by_capability["skill_registry"]["ready_tools"])
            self.assertNotIn("definitely_not_a_real_capability", by_capability)

    def test_tool_and_skill_queries_do_not_treat_source_presence_as_runtime_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            system = self.make_system(tmp)
            tools = system.tools(ready_only=True)
            self.assertGreater(tools["count"], 0)
            self.assertTrue(all(item["adapter_ready"] for item in tools["tools"]))
            self.assertIn("source code presence alone", tools["note"])

            skills = system.skills(ready_only=True)
            self.assertGreater(skills["count"], 0)
            self.assertTrue(all(item["ready"] for item in skills["skills"]))

    def test_permissions_are_descriptive_and_never_granted_by_introspection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            system = self.make_system(tmp)
            payload = system.permissions()
            self.assertEqual("descriptive_only", payload["authority"])
            self.assertEqual("not_exposed_by_this_api", payload["grants"])
            self.assertTrue(payload["permissions"])
            self.assertTrue(all(not item["granted_by_introspection"] for item in payload["permissions"]))
            by_name = {item["permission"]: item for item in payload["permissions"]}
            self.assertIn("source.write.with_confirmation", by_name)
            self.assertTrue(by_name["source.write.with_confirmation"]["write_like"])
            self.assertTrue(by_name["source.write.with_confirmation"]["confirmation_declared"])

    def test_project_state_whitelists_metadata_without_exposing_data_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            system = self.make_system(tmp)
            with patch.dict(
                os.environ,
                {
                    "RESEARCH_OS_BUILD_SHA": "a" * 40,
                    "RESEARCH_OS_CHANNEL": "feature-test",
                    "RESEARCH_OS_VERSION": "2.0.0-rc.2-dev",
                    "RESEARCH_OS_DATA_DIR": "C:/secret/private/path",
                },
                clear=False,
            ):
                payload = system.project_state()
            self.assertEqual("a" * 40, payload["build"]["sha"])
            self.assertEqual("feature-test", payload["build"]["channel"])
            self.assertTrue(payload["storage"]["data_dir_configured"])
            self.assertFalse(payload["storage"]["data_dir_exposed"])
            self.assertNotIn("C:/secret/private/path", repr(payload))
            self.assertFalse(payload["authority"]["release_state_authoritative"])

    def test_plan_is_read_only_json_safe_and_scrubs_credential_patterns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            system = self.make_system(tmp)
            secret = "sk-phase7secretvalue123456"
            payload = system.plan(
                f"analyze constraints for API work using {secret}",
                session_id="phase7-plan",
                context={"project": "Research OS"},
            )
            self.assertTrue(payload["read_only"])
            self.assertFalse(payload["execution_performed"])
            self.assertIsInstance(payload["result"]["plan"], dict)
            self.assertNotIn(secret, repr(payload))
            self.assertIn("[REDACTED]", repr(payload))

    def test_health_requires_real_ready_registries_without_claiming_execution_bypass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            system = self.make_system(tmp)
            health = system.health()
            self.assertTrue(health["ready"])
            self.assertGreaterEqual(health["counts"]["brain_agents_ready"], 10)
            self.assertGreater(health["counts"]["skills_ready"], 0)
            self.assertGreater(health["counts"]["tools_ready"], 0)
            self.assertTrue(health["safety"]["mutation_requires_execution_controller"])
            self.assertFalse(health["safety"]["direct_adapter_access"])

    def test_invalid_scope_and_oversized_plan_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            system = self.make_system(tmp)
            with self.assertRaisesRegex(ValueError, "scope must be"):
                system.agents(scope="everything")
            with self.assertRaisesRegex(ValueError, "objective exceeds"):
                system.plan("x" * 8001)


if __name__ == "__main__":
    unittest.main()
