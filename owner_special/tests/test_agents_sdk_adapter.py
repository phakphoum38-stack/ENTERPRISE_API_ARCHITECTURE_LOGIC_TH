import unittest

from owner_special.research_os_friend import (
    AgentsSdkAdapter,
    ApprovalState,
    FriendRequest,
    FriendRuntime,
    Tool,
)


class AgentsSdkAdapterTests(unittest.TestCase):
    def test_contract_is_deterministic_and_read_only(self):
        runtime = FriendRuntime.create_owner_special("owner-sdk")
        runtime.orchestrator.tools.register(
            Tool("safe.lookup", "safe lookup", lambda text: text)
        )
        request = FriendRequest(owner_id="owner-sdk", text="hello", requested_tools=("safe.lookup",))

        contract = AgentsSdkAdapter(runtime.orchestrator).build_contract(request)

        self.assertEqual(contract.agent_name, "research-os-friend")
        self.assertEqual(contract.owner_id, "owner-sdk")
        self.assertEqual(len(contract.tools), 1)
        self.assertEqual(contract.tools[0].name, "safe.lookup")
        self.assertEqual(contract.tools[0].approval_state, ApprovalState.NOT_REQUIRED.value)
        self.assertFalse(contract.tools[0].approval_required)

    def test_side_effect_tool_contract_reports_pending_approval(self):
        runtime = FriendRuntime.create_owner_special("owner-sdk")
        runtime.orchestrator.tools.register(
            Tool("shell.run", "side effect", lambda text: text)
        )
        request = FriendRequest(owner_id="owner-sdk", text="run command", requested_tools=("shell.run",))

        contract = AgentsSdkAdapter(runtime.orchestrator).build_contract(request)

        self.assertTrue(contract.tools[0].approval_required)
        self.assertEqual(contract.tools[0].approval_state, ApprovalState.PENDING.value)

    def test_wrong_owner_cannot_build_contract(self):
        runtime = FriendRuntime.create_owner_special("owner-sdk")
        request = FriendRequest(owner_id="other-owner", text="hello")
        with self.assertRaises(PermissionError):
            AgentsSdkAdapter(runtime.orchestrator).build_contract(request)

    def test_adapter_does_not_require_credentials(self):
        runtime = FriendRuntime.create_owner_special("owner-sdk")
        status = AgentsSdkAdapter(runtime.orchestrator).sdk_dependency_status()
        self.assertFalse(status["api_calls"])
        self.assertFalse(status["credential_required_for_this_phase"])
        self.assertEqual(status["execution_authority"], "FriendOrchestrator")


if __name__ == "__main__":
    unittest.main()
