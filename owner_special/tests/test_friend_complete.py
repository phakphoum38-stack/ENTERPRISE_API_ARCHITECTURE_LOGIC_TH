import json
import tempfile
import unittest
from pathlib import Path

from research_os_friend import FriendRequest, FriendRuntime


class FriendCompleteTests(unittest.TestCase):
    def test_owner_boundary_rejects_other_owner(self) -> None:
        runtime = FriendRuntime.create_owner_special("phakphum")
        with self.assertRaises(PermissionError):
            runtime.ask(FriendRequest(owner_id="someone-else", text="hello"))

    def test_complete_architecture_is_installed(self) -> None:
        runtime = FriendRuntime.create_owner_special("phakphum")
        architecture = runtime.architecture()
        self.assertEqual(architecture["edition"], "owner-special")
        self.assertEqual(architecture["brain_profiles"]["6^6"], 46656)
        self.assertGreaterEqual(len(architecture["skills"]), 10)
        self.assertIn("security", architecture["skills"])
        self.assertIn("quality", architecture["skills"])
        self.assertEqual(architecture["memory_scope"], "owner/profile/session")

    def test_adaptive_brain_reaches_6_to_6_logical_capacity(self) -> None:
        runtime = FriendRuntime.create_owner_special("phakphum")
        response = runtime.ask(
            FriendRequest(
                owner_id="phakphum",
                text="large project",
                complexity=9,
                risk=7,
                parallelism=8,
                requested_skills=("analysis", "planning", "coding", "quality"),
            )
        )
        self.assertEqual(response.decision.scale.value, "6^6")
        self.assertEqual(response.decision.maximum_leaf_capacity, 46656)

    def test_memory_isolated_by_profile_and_session(self) -> None:
        runtime = FriendRuntime.create_owner_special("phakphum")
        runtime.ask(FriendRequest(owner_id="phakphum", profile_id="work", session_id="a", text="A"))
        runtime.ask(FriendRequest(owner_id="phakphum", profile_id="home", session_id="b", text="B"))
        memory = runtime.orchestrator.memory
        self.assertEqual(len(memory.recall(owner_id="phakphum", profile_id="work", session_id="a")), 2)
        self.assertEqual(len(memory.recall(owner_id="phakphum", profile_id="home", session_id="b")), 2)
        self.assertEqual(len(memory.recall(owner_id="phakphum", profile_id="work", session_id="b")), 0)

    def test_requested_skill_and_tool_are_routed(self) -> None:
        runtime = FriendRuntime.create_owner_special("phakphum")
        response = runtime.ask(
            FriendRequest(
                owner_id="phakphum",
                text="inspect this",
                requested_skills=("analysis", "security"),
                requested_tools=("echo",),
            )
        )
        self.assertEqual(response.decision.selected_skills, ("analysis", "security"))
        self.assertEqual(response.decision.selected_tools, ("echo",))
        self.assertEqual(response.provider, "owner-mock")

    def test_evidence_redacts_credential_like_values(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence_path = Path(temporary) / "evidence.jsonl"
            runtime = FriendRuntime.create_owner_special("phakphum", evidence_path=evidence_path)
            runtime.orchestrator.evidence.record(
                owner_id="phakphum",
                profile_id="default",
                session_id="default",
                event="redaction-test",
                data={"value": "sk-abcdefghijklmnopqrstuv"},
            )
            record = json.loads(evidence_path.read_text(encoding="utf-8").splitlines()[-1])
            self.assertEqual(record["data"]["value"], "[REDACTED]")

    def test_reasoning_is_summary_not_hidden_trace(self) -> None:
        runtime = FriendRuntime.create_owner_special("phakphum")
        response = runtime.ask(FriendRequest(owner_id="phakphum", text="plan", complexity=4))
        self.assertTrue(response.decision.summary)
        self.assertIn("adaptive capacity", response.decision.summary)
        self.assertNotIn("chain-of-thought", response.metadata)


if __name__ == "__main__":
    unittest.main()
