import tempfile
import unittest
from pathlib import Path

from owner_special.research_os_friend import AgentRunStatus, FriendRequest, FriendRuntime


class AgentRuntimeTests(unittest.TestCase):
    def test_agent_runtime_records_lifecycle_and_evidence(self):
        runtime = FriendRuntime.create_owner_special("owner-agent-runtime")
        run = runtime.run_agent(
            FriendRequest(
                owner_id="owner-agent-runtime",
                profile_id="default",
                session_id="session-1",
                text="hello friend",
            )
        )

        self.assertEqual(run.status, AgentRunStatus.COMPLETED)
        self.assertEqual(
            [event.event for event in run.events],
            ["run-created", "planning", "executing", "verifying", "completed"],
        )
        self.assertIsNotNone(run.response)
        self.assertEqual(run.events[-1].data["evidence_id"], run.response.evidence_id)
        self.assertEqual(runtime.get_agent_run(run.run_id), run)
        self.assertEqual(runtime.agent_runs(), (run,))

    def test_agent_runtime_preserves_owner_boundary_on_failure(self):
        runtime = FriendRuntime.create_owner_special("owner-agent-runtime")
        run = runtime.run_agent(
            FriendRequest(owner_id="another-owner", text="hello friend")
        )

        self.assertEqual(run.status, AgentRunStatus.FAILED)
        self.assertEqual(run.events[-1].event, "failed")
        self.assertIsNotNone(run.error)
        self.assertEqual(runtime.agent_runs(), ())

    def test_architecture_reports_agent_runtime_without_mutating_core_skills(self):
        runtime = FriendRuntime.create_owner_special("owner-agent-runtime")
        core_before = runtime.orchestrator.skills.names()
        architecture = runtime.architecture()

        self.assertTrue(architecture["agent_runtime"]["enabled"])
        self.assertEqual(architecture["agent_runtime"]["trace"], "in-process immutable events")
        self.assertEqual(runtime.orchestrator.skills.names(), core_before)

    def test_agent_trace_survives_runtime_restart_and_remains_owner_scoped(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = FriendRuntime.create_owner_special("owner-a", data_root=root)
            run = runtime.run_agent(FriendRequest(owner_id="owner-a", text="persist this run"))

            restarted = FriendRuntime.create_owner_special("owner-a", data_root=root)
            recovered = restarted.get_agent_run(run.run_id)
            self.assertIsNotNone(recovered)
            self.assertEqual(recovered.status, AgentRunStatus.COMPLETED)
            self.assertEqual(recovered.response, None)
            self.assertEqual(restarted.agent_runs(), (recovered,))
            self.assertTrue((root / "owners" / "owner-a" / "agent" / "traces.json").is_file())

            other_owner = FriendRuntime.create_owner_special("owner-b", data_root=root)
            self.assertIsNone(other_owner.get_agent_run(run.run_id))
            self.assertEqual(other_owner.agent_runs(), ())


if __name__ == "__main__":
    unittest.main()
