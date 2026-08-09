import unittest

from agent_platform import AGENTS, AgentRegistry
from v2_completion_crew import COMPLETION_CREW, register_completion_crew


class V2CompletionCrewTests(unittest.TestCase):
    def test_completion_crew_is_new_and_does_not_replace_active_agents(self):
        registry = AgentRegistry()
        active_before = {item.agent_id for item in AGENTS}
        active_objects = {item.agent_id: registry.get(item.agent_id) for item in AGENTS}

        registered = register_completion_crew(registry)
        crew_ids = {item.agent_id for item in COMPLETION_CREW}

        self.assertEqual(
            crew_ids,
            {
                "v2_workspace_engineer",
                "v2_agent_center_engineer",
                "v2_api_compat_engineer",
                "v2_reliability_release_engineer",
            },
        )
        self.assertTrue(active_before.isdisjoint(crew_ids))
        self.assertEqual(len(registered), 4)
        self.assertEqual(registry.readiness()["agent_count"], len(active_before) + 4)

        for agent_id, original in active_objects.items():
            self.assertEqual(registry.get(agent_id), original)

    def test_each_completion_agent_has_isolated_scope_and_no_fallback(self):
        scopes = [item.memory_scope for item in COMPLETION_CREW]
        self.assertEqual(len(scopes), len(set(scopes)))
        for item in COMPLETION_CREW:
            self.assertTrue(item.memory_scope.startswith("shared:v2-"))
            self.assertEqual(item.fallback_agents, ())
            self.assertEqual(item.permission_profile, "write_confirmed")


if __name__ == "__main__":
    unittest.main()
