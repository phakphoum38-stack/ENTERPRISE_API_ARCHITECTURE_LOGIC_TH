import unittest

from tools import validate_research_os_capability_convergence as validator


class ResearchOSCapabilityConvergenceTests(unittest.TestCase):
    def test_validator_passes(self):
        self.assertEqual(validator.main(), 0)

    def test_navigation_has_six_explicit_bindings(self):
        entries = validator._navigation_entries(validator.NAVIGATION.read_text(encoding="utf-8"))
        bound = {
            destination: capability
            for destination, (_, capability) in entries.items()
            if capability is not None
        }
        self.assertEqual(
            bound,
            {
                "agent_center": "agent",
                "github": "github",
                "friend_connect": "friend",
                "workflows": "factory_v3",
                "control_center": "control_center",
                "owner": "owner",
            },
        )

    def test_owner_is_not_required_to_exist_in_backend_capability_registry(self):
        contract = validator.json.loads(
            validator.CONTRACT.read_text(encoding="utf-8")
        )
        owner = next(item for item in contract["bindings"] if item["destination_id"] == "owner")
        self.assertEqual(owner["authority"], "owner_experience_contract")
        self.assertEqual(owner["capability_id"], "owner")

    def test_unbound_destinations_hold(self):
        entries = validator._navigation_entries(validator.NAVIGATION.read_text(encoding="utf-8"))
        contract = validator.json.loads(
            validator.CONTRACT.read_text(encoding="utf-8")
        )
        bound = {item["destination_id"] for item in contract["bindings"]}
        self.assertEqual(set(entries) - bound, {
            "home",
            "ai_chat",
            "brain_skills",
            "library",
            "knowledge_graph",
            "google_workspace",
            "local_api_service",
            "system_monitor",
            "settings",
            "developer_access",
            "google_sign_in",
            "projects",
        })


if __name__ == "__main__":
    unittest.main()
