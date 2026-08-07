import unittest

from agent_platform import AGENTS, AgentRegistry, AgentRouter, platform_dashboard


class AgentPlatformTest(unittest.TestCase):
    def test_registry_contains_initial_agents(self):
        ids = {agent.agent_id for agent in AGENTS}
        self.assertEqual(ids, {"research", "document", "github", "google_workspace", "shift"})
        self.assertEqual(platform_dashboard()["agent_count"], 5)

    def test_routes_shift_work_to_shift_agent(self):
        result = AgentRouter().route("analyze shift roster replacement leave conflict")
        self.assertEqual(result["agent"]["agent_id"], "shift")
        self.assertTrue(result["requires_confirmation_for_writes"])

    def test_routes_github_work_to_github_agent(self):
        result = AgentRouter().route("review github repository pull_request workflow")
        self.assertEqual(result["agent"]["agent_id"], "github")

    def test_unknown_work_falls_back_to_research(self):
        result = AgentRouter().route("explore an unfamiliar topic")
        self.assertEqual(result["agent"]["agent_id"], "research")
        self.assertEqual(result["reason"], "default")

    def test_explicit_agent_selection(self):
        result = AgentRouter(AgentRegistry()).route("anything", requested_agent="document")
        self.assertEqual(result["agent"]["agent_id"], "document")
        self.assertEqual(result["reason"], "explicit")


if __name__ == "__main__":
    unittest.main()
