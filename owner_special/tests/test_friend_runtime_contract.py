import os
import unittest

from owner_special.research_os_friend import FriendRequest, FriendRuntime
from owner_special.research_os_friend.friend_runtime_contract import (
    FriendRuntimeContract,
    FriendRuntimeContractError,
)


SOURCE_SHA = "0123456789abcdef0123456789abcdef01234567"


class FriendRuntimeContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.previous_sha = os.environ.get("RESEARCH_OS_SOURCE_SHA")
        os.environ["RESEARCH_OS_SOURCE_SHA"] = SOURCE_SHA
        self.runtime = FriendRuntime.create_owner_special("owner-h4")
        self.contract = FriendRuntimeContract(
            self.runtime,
            owner_id="owner-h4",
            expected_source_sha=SOURCE_SHA,
        )

    def tearDown(self) -> None:
        if self.previous_sha is None:
            os.environ.pop("RESEARCH_OS_SOURCE_SHA", None)
        else:
            os.environ["RESEARCH_OS_SOURCE_SHA"] = self.previous_sha

    def test_snapshot_is_bound_and_read_only(self) -> None:
        snapshot = self.contract.snapshot()
        self.assertEqual(snapshot["schema"], "research-os-friend-runtime/v1")
        self.assertEqual(snapshot["owner_id"], "owner-h4")
        self.assertEqual(snapshot["source_sha"], SOURCE_SHA)
        self.assertTrue(snapshot["read_only"])

    def test_wrong_source_sha_is_rejected(self) -> None:
        with self.assertRaises(FriendRuntimeContractError):
            FriendRuntimeContract(
                self.runtime,
                owner_id="owner-h4",
                expected_source_sha="fedcba9876543210fedcba9876543210fedcba98",
            )

    def test_missing_runtime_source_is_rejected(self) -> None:
        self.runtime.source_commit = ""
        with self.assertRaises(FriendRuntimeContractError):
            FriendRuntimeContract(
                self.runtime,
                owner_id="owner-h4",
                expected_source_sha=SOURCE_SHA,
            )

    def test_wrong_owner_request_is_rejected(self) -> None:
        request = FriendRequest(owner_id="other-owner", text="should fail")
        with self.assertRaises(FriendRuntimeContractError):
            self.contract.ask(request)

    def test_correlation_id_is_required_for_agent_run(self) -> None:
        request = FriendRequest(owner_id="owner-h4", text="runtime contract smoke")
        with self.assertRaises(FriendRuntimeContractError):
            self.contract.run_agent(request, run_correlation_id="bad correlation")

    def test_agent_run_returns_bound_envelope(self) -> None:
        request = FriendRequest(owner_id="owner-h4", text="runtime contract smoke")
        result = self.contract.run_agent(request, run_correlation_id="h4.test.run")
        self.assertEqual(result["schema"], "research-os-friend-runtime/v1")
        self.assertEqual(result["owner_id"], "owner-h4")
        self.assertEqual(result["source_sha"], SOURCE_SHA)
        self.assertEqual(result["run_correlation_id"], "h4.test.run")
        self.assertTrue(result["read_only"])

    def test_secret_like_output_is_rejected(self) -> None:
        with self.assertRaises(FriendRuntimeContractError):
            self.contract._validate_payload({"api_key": "blocked"})

    def test_dynamic_output_is_rejected(self) -> None:
        with self.assertRaises(FriendRuntimeContractError):
            self.contract._validate_payload({"value": lambda: None})

    def test_snapshot_result_is_defensively_copied(self) -> None:
        first = self.contract.snapshot()
        first["agent_runs"].append({"run_id": "mutated"})
        second = self.contract.snapshot()
        self.assertEqual(second["agent_runs"], [])

    def test_tool_health_is_read_only_projection(self) -> None:
        result = self.contract.tool_health()
        self.assertIsInstance(result, dict)


if __name__ == "__main__":
    unittest.main()
