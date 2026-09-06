import unittest

from owner_special.research_os_friend.agent_runtime import AgentRunStatus, AgentRuntime
from owner_special.research_os_friend.mission_control import MissionControl
from owner_special.research_os_friend.runtime import FriendRuntime


class MissionControlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = FriendRuntime.create_owner_special("owner-mission", data_root=None)
        self.agent = self.runtime.agent_runtime
        assert self.agent is not None
        self.control = MissionControl(self.agent)

    def test_snapshot_is_read_only_and_owner_scoped(self) -> None:
        request = self._request("owner-mission", "Inspect the workspace")
        run = self.agent.run(request)

        snapshot = self.control.snapshot(limit=10)

        self.assertEqual(snapshot["schema"], "research-os-mission-control/v1")
        self.assertTrue(snapshot["read_only"])
        self.assertEqual(snapshot["execution_authority"], "FriendOrchestrator")
        self.assertEqual(snapshot["authorization_authority"], "OwnerPolicy")
        self.assertEqual(snapshot["approval_authority"], "ApprovalGate")
        self.assertEqual(snapshot["total_runs"], 1)
        self.assertEqual(snapshot["runs"][0]["run_id"], run.run_id)
        self.assertEqual(snapshot["runs"][0]["status"], AgentRunStatus.COMPLETED.value)

        self.assertIsNotNone(self.control.run(run.run_id, owner_id="owner-mission"))
        self.assertIsNone(self.control.run(run.run_id, owner_id="other-owner"))

    def test_limit_is_bounded(self) -> None:
        with self.assertRaises(ValueError):
            self.control.snapshot(limit=0)
        with self.assertRaises(ValueError):
            self.control.snapshot(limit=MissionControl.MAX_RUNS + 1)

    @staticmethod
    def _request(owner_id: str, text: str):
        from owner_special.research_os_friend.models import FriendRequest

        return FriendRequest(
            owner_id=owner_id,
            profile_id="default",
            session_id="mission-session",
            text=text,
        )


if __name__ == "__main__":
    unittest.main()
