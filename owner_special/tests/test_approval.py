import unittest

from owner_special.research_os_friend import (
    ApprovalGate,
    ApprovalState,
    FriendRequest,
    FriendRuntime,
    OwnerIdentity,
    Tool,
)


class ApprovalGateTests(unittest.TestCase):
    def setUp(self):
        self.owner = OwnerIdentity(owner_id="owner-approval", display_name="Owner")
        self.gate = ApprovalGate()

    def request(self, *, tool="shell.run", owner_id="owner-approval", text="run command"):
        return FriendRequest(
            owner_id=owner_id,
            profile_id="default",
            session_id="session-1",
            text=text,
            requested_tools=(tool,),
        )

    def test_side_effect_tool_starts_pending(self):
        record = self.gate.inspect(self.owner, self.request())
        self.assertEqual(record.state, ApprovalState.PENDING)
        self.assertEqual(self.gate.get(record.approval_id), record)

    def test_pending_tool_cannot_execute(self):
        request = self.request()
        with self.assertRaisesRegex(PermissionError, "approval required"):
            self.gate.enforce(self.owner, request, "shell.run")

    def test_approval_is_bound_to_exact_request(self):
        request = self.request()
        approved = self.gate.approve(self.owner, request, "shell.run", reason="owner approved")
        self.assertEqual(approved.state, ApprovalState.APPROVED)
        self.assertEqual(self.gate.enforce(self.owner, request, "shell.run"), approved)
        changed = self.request(text="run a different command")
        with self.assertRaisesRegex(PermissionError, "approval required"):
            self.gate.enforce(self.owner, changed, "shell.run")

    def test_denial_is_terminal_for_exact_request(self):
        request = self.request()
        denied = self.gate.deny(self.owner, request, "shell.run", reason="unsafe")
        self.assertEqual(denied.state, ApprovalState.DENIED)
        with self.assertRaisesRegex(PermissionError, "execution denied"):
            self.gate.enforce(self.owner, request, "shell.run")

    def test_safe_tool_does_not_require_approval(self):
        request = self.request(tool="echo")
        record = self.gate.inspect(self.owner, request, "echo")
        self.assertEqual(record.state, ApprovalState.NOT_REQUIRED)
        self.assertEqual(self.gate.enforce(self.owner, request, "echo"), record)

    def test_owner_boundary_is_enforced(self):
        request = self.request(owner_id="other-owner")
        with self.assertRaises(PermissionError):
            self.gate.inspect(self.owner, request, "shell.run")

    def test_orchestrator_blocks_side_effect_before_handler_and_allows_after_approval(self):
        runtime = FriendRuntime.create_owner_special("owner-approval")
        calls = []

        runtime.orchestrator.tools.register(
            Tool(
                name="shell.run",
                description="test side-effect tool",
                handler=lambda text: calls.append(text) or '{"ok":true}',
            )
        )
        request = self.request()
        with self.assertRaisesRegex(PermissionError, "approval required"):
            runtime.ask(request)
        self.assertEqual(calls, [])

        runtime.orchestrator.approval_gate.approve(
            runtime.owner,
            request,
            "shell.run",
            reason="test approval",
        )
        runtime.ask(request)
        self.assertEqual(calls, ["run command"])


if __name__ == "__main__":
    unittest.main()
