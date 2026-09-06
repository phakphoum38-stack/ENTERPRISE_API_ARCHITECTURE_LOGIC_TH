import unittest

from owner_special.research_os_friend import (
    ApprovalState,
    ComputerActionIntent,
    ComputerActionType,
    ComputerUseBoundary,
    FriendRequest,
    OwnerIdentity,
)


class ComputerUseBoundaryTests(unittest.TestCase):
    def test_plan_requires_matching_owner(self):
        boundary = ComputerUseBoundary()
        owner = OwnerIdentity(owner_id="owner-computer", display_name="Owner")
        request = FriendRequest(owner_id="owner-computer", text="open the app")
        plan = boundary.plan(
            owner,
            request,
            actions=(ComputerActionIntent(ComputerActionType.CLICK, "click the app"),),
        )
        self.assertEqual(plan.approval_state, ApprovalState.PENDING)
        self.assertEqual(len(plan.actions), 1)

    def test_computer_use_cannot_be_marked_not_required(self):
        boundary = ComputerUseBoundary()
        owner = OwnerIdentity(owner_id="owner-computer", display_name="Owner")
        request = FriendRequest(owner_id="owner-computer", text="type a value")
        with self.assertRaises(ValueError):
            boundary.plan(
                owner,
                request,
                actions=(ComputerActionIntent(ComputerActionType.TYPE, "type value"),),
                approval_state=ApprovalState.NOT_REQUIRED,
            )

    def test_wrong_owner_is_rejected(self):
        boundary = ComputerUseBoundary()
        owner = OwnerIdentity(owner_id="owner-computer", display_name="Owner")
        request = FriendRequest(owner_id="other-owner", text="open the app")
        with self.assertRaises(PermissionError):
            boundary.plan(owner, request, actions=())

    def test_boundary_does_not_execute_computer_operations(self):
        status = ComputerUseBoundary().execution_status()
        self.assertFalse(status["os_input"])
        self.assertFalse(status["screenshots"])
        self.assertFalse(status["api_calls"])
        self.assertTrue(status["approval_required_by_default"])


if __name__ == "__main__":
    unittest.main()
