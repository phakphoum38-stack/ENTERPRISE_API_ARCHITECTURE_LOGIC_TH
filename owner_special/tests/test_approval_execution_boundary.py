from __future__ import annotations

import unittest

from owner_special.research_os_friend.identity import OwnerIdentity
from owner_special.research_os_friend.models import FriendRequest
from owner_special.research_os_friend.orchestrator import FriendOrchestrator


class _PolicySpy:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def authorize_tool(self, owner: OwnerIdentity, request: FriendRequest, tool_name: str) -> None:
        self.calls.append(("authorize_tool", tool_name))


class _ApprovalSpy:
    def __init__(self, required: set[str], *, allow: bool = True) -> None:
        self.required = required
        self.allow = allow
        self.calls: list[str] = []

    def requires_approval(self, tool_name: str) -> bool:
        return tool_name in self.required

    def enforce(self, owner: OwnerIdentity, request: FriendRequest, tool_name: str) -> None:
        self.calls.append(tool_name)
        if not self.allow:
            raise PermissionError("approval denied")


class ApprovalExecutionBoundaryTests(unittest.TestCase):
    def _orchestrator(self, policy: _PolicySpy, approval: _ApprovalSpy) -> FriendOrchestrator:
        orchestrator = object.__new__(FriendOrchestrator)
        orchestrator.owner = OwnerIdentity("owner")
        orchestrator.policy = policy
        orchestrator.approval_gate = approval
        return orchestrator

    def test_explicit_tool_requires_policy_and_approval_before_execution(self) -> None:
        policy = _PolicySpy()
        approval = _ApprovalSpy({"shell.run"})
        orchestrator = self._orchestrator(policy, approval)
        request = FriendRequest(owner_id="owner", text="run", requested_tools=("shell.run",))

        orchestrator._authorize_tool_execution(request, "shell.run")

        self.assertEqual(policy.calls, [("authorize_tool", "shell.run")])
        self.assertEqual(approval.calls, ["shell.run"])

    def test_implicit_side_effect_tool_is_blocked(self) -> None:
        policy = _PolicySpy()
        approval = _ApprovalSpy({"shell.run"})
        orchestrator = self._orchestrator(policy, approval)
        request = FriendRequest(owner_id="owner", text="run")

        with self.assertRaisesRegex(PermissionError, "explicitly requested and approved"):
            orchestrator._authorize_tool_execution(request, "shell.run")

        self.assertEqual(policy.calls, [])
        self.assertEqual(approval.calls, [])

    def test_implicit_read_only_tool_remains_allowed(self) -> None:
        policy = _PolicySpy()
        approval = _ApprovalSpy({"shell.run"})
        orchestrator = self._orchestrator(policy, approval)
        request = FriendRequest(owner_id="owner", text="inspect")

        orchestrator._authorize_tool_execution(request, "github.repository_status")

        self.assertEqual(policy.calls, [])
        self.assertEqual(approval.calls, [])

    def test_explicit_denial_stops_at_approval_gate(self) -> None:
        policy = _PolicySpy()
        approval = _ApprovalSpy({"shell.run"}, allow=False)
        orchestrator = self._orchestrator(policy, approval)
        request = FriendRequest(owner_id="owner", text="run", requested_tools=("shell.run",))

        with self.assertRaisesRegex(PermissionError, "approval denied"):
            orchestrator._authorize_tool_execution(request, "shell.run")

        self.assertEqual(policy.calls, [("authorize_tool", "shell.run")])
        self.assertEqual(approval.calls, ["shell.run"])


if __name__ == "__main__":
    unittest.main()
