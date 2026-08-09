import unittest

from agent_platform import (
    AGENTS,
    AgentDefinition,
    AgentRegistry,
    AgentRouter,
    platform_dashboard,
)


class AgentPlatformTest(unittest.TestCase):
    def test_registry_contains_initial_agents(self):
        ids = {agent.agent_id for agent in AGENTS}
        self.assertEqual(
            ids,
            {"research", "developer", "document", "github", "google_workspace", "shift"},
        )
        dashboard = platform_dashboard()
        self.assertEqual(dashboard["agent_count"], 6)
        self.assertEqual(dashboard["ready_agent_count"], 6)
        self.assertEqual(dashboard["dynamic_registration"], "active")

    def test_routes_shift_work_to_shift_agent(self):
        result = AgentRouter().route("analyze shift roster replacement leave conflict")
        self.assertEqual(result["agent"]["agent_id"], "shift")
        self.assertTrue(result["requires_confirmation_for_writes"])
        self.assertTrue(result["health"]["ready"])

    def test_routes_github_work_to_github_agent(self):
        result = AgentRouter().route("review github repository pull_request workflow")
        self.assertEqual(result["agent"]["agent_id"], "github")

    def test_routes_developer_work_to_developer_agent(self):
        result = AgentRouter().route("debug code api build test architecture")
        self.assertEqual(result["agent"]["agent_id"], "developer")
        self.assertTrue(result["requires_confirmation_for_writes"])

    def test_unknown_work_falls_back_to_research(self):
        result = AgentRouter().route("explore an unfamiliar topic")
        self.assertEqual(result["agent"]["agent_id"], "research")
        self.assertEqual(result["reason"], "default")

    def test_explicit_agent_selection(self):
        result = AgentRouter(AgentRegistry()).route("anything", requested_agent="document")
        self.assertEqual(result["agent"]["agent_id"], "document")
        self.assertEqual(result["reason"], "explicit")

    def test_dynamic_registration_and_capability_discovery(self):
        registry = AgentRegistry()
        registry.register(
            AgentDefinition(
                "security_review",
                "Security Review Agent",
                "Reviews application security evidence.",
                ("security_review", "threat_model"),
                ("source.read", "security.read"),
                "shared:security-review",
            )
        )

        discovered = registry.discover(capability="threat_model")
        self.assertEqual(len(discovered), 1)
        self.assertEqual(discovered[0]["agent_id"], "security_review")
        self.assertTrue(discovered[0]["health"]["ready"])

        routed = AgentRouter(registry).route("prepare threat_model security_review")
        self.assertEqual(routed["agent"]["agent_id"], "security_review")

        removed = registry.unregister("security_review")
        self.assertEqual(removed["agent_id"], "security_review")
        with self.assertRaisesRegex(ValueError, "unknown agent"):
            registry.get("security_review")

    def test_router_skips_unavailable_agent(self):
        registry = AgentRegistry()
        registry.set_health("github", "unavailable", reason="connector offline")

        with self.assertRaisesRegex(ValueError, "agent unavailable"):
            AgentRouter(registry).route("github repository", requested_agent="github")

        result = AgentRouter(registry).route("github repository workflow")
        self.assertNotEqual(result["agent"]["agent_id"], "github")
        self.assertTrue(result["health"]["ready"])

        readiness = registry.readiness()
        self.assertEqual(readiness["unavailable_count"], 1)
        self.assertEqual(readiness["ready_count"], 5)

    def test_degraded_agent_remains_routable(self):
        registry = AgentRegistry()
        health = registry.set_health("document", "degraded", reason="slow parser")
        self.assertTrue(health["ready"])
        result = AgentRouter(registry).route("pdf document_read classify")
        self.assertEqual(result["agent"]["agent_id"], "document")
        self.assertEqual(result["health"]["status"], "degraded")


if __name__ == "__main__":
    unittest.main()
