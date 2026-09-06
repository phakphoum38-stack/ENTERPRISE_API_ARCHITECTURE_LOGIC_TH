import unittest

from owner_special.research_os_friend.mission_control_capabilities import MissionControlCapabilities
from owner_special.research_os_friend.runtime import FriendRuntime


class MissionControlCapabilitiesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = FriendRuntime.create_owner_special("owner-capabilities", data_root=None)
        self.control = MissionControlCapabilities(self.runtime)

    def test_snapshot_projects_existing_health_without_execution_authority(self) -> None:
        snapshot = self.control.snapshot(limit=5)

        self.assertEqual(snapshot["schema"], "research-os-mission-control-capabilities/v1")
        self.assertEqual(snapshot["owner_id"], "owner-capabilities")
        self.assertTrue(snapshot["read_only"])
        self.assertEqual(snapshot["execution_authority"], "FriendOrchestrator")
        self.assertEqual(snapshot["authorization_authority"], "OwnerPolicy")
        self.assertEqual(snapshot["approval_authority"], "ApprovalGate")
        self.assertEqual(snapshot["total"], 15)
        self.assertEqual(snapshot["healthy"], 7)
        self.assertEqual(snapshot["limit"], 5)
        self.assertTrue(snapshot["truncated"])
        self.assertEqual(
            [row["name"] for row in snapshot["rows"]],
            ["echo", "file", "git-branch", "github", "github-actions"],
        )

    def test_limit_is_bounded(self) -> None:
        with self.assertRaises(ValueError):
            self.control.snapshot(limit=0)
        with self.assertRaises(ValueError):
            self.control.snapshot(limit=MissionControlCapabilities.MAX_ROWS + 1)


if __name__ == "__main__":
    unittest.main()
