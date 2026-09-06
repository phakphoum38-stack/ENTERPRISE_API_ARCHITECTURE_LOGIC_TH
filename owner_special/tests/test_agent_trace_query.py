import tempfile
import unittest
from pathlib import Path

from owner_special.research_os_friend import AgentRunStatus, FriendRequest, FriendRuntime


class AgentTraceQueryTests(unittest.TestCase):
    def test_persistent_trace_query_supports_session_status_and_pagination(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = FriendRuntime.create_owner_special("owner-trace-query", data_root=root)
            first = runtime.run_agent(
                FriendRequest(owner_id="owner-trace-query", session_id="a", text="first")
            )
            second = runtime.run_agent(
                FriendRequest(owner_id="owner-trace-query", session_id="b", text="second")
            )
            third = runtime.run_agent(
                FriendRequest(owner_id="owner-trace-query", session_id="a", text="third")
            )

            page = runtime.agent_runs(limit=2, offset=0)
            self.assertEqual(len(page), 2)
            self.assertEqual({item.run_id for item in page}, {third.run_id, second.run_id})

            session_a = runtime.agent_runs(session_id="a")
            self.assertEqual({item.run_id for item in session_a}, {first.run_id, third.run_id})

            completed = runtime.agent_runs(status=AgentRunStatus.COMPLETED)
            self.assertEqual(len(completed), 3)
            self.assertEqual(runtime.agent_runs(limit=0), ())

    def test_in_process_runtime_keeps_query_semantics(self):
        runtime = FriendRuntime.create_owner_special("owner-trace-query")
        runtime.run_agent(FriendRequest(owner_id="owner-trace-query", session_id="a", text="one"))
        runtime.run_agent(FriendRequest(owner_id="owner-trace-query", session_id="b", text="two"))
        self.assertEqual(len(runtime.agent_runs(session_id="a")), 1)
        self.assertEqual(len(runtime.agent_runs(limit=1, offset=1)), 1)


if __name__ == "__main__":
    unittest.main()
