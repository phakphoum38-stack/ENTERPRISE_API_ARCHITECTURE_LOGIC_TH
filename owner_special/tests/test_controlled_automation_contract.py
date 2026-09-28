import unittest

from owner_special.research_os_friend.controlled_automation_contract import (
    AutomationDecision,
    AutomationRequest,
    ControlledAutomationContract,
    ControlledAutomationError,
)


SOURCE_SHA = "0123456789abcdef0123456789abcdef01234567"


class ControlledAutomationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = ControlledAutomationContract()

    def request(self, **overrides):
        values = {
            "owner_id": "owner-h6",
            "source_sha": SOURCE_SHA,
            "correlation_id": "h6.test.run",
            "capability": "READ_WEB",
            "action": "fetch",
            "target": "https://example.com/docs",
            "side_effect": False,
            "dry_run": True,
        }
        values.update(overrides)
        return AutomationRequest(**values)

    def test_allowlisted_read_only_request_is_allowed_without_executor_authority(self) -> None:
        result = self.contract.decide(self.request(), allowed_hosts=("example.com",))
        self.assertEqual(result["decision"], AutomationDecision.ALLOW_READ_ONLY.value)
        self.assertFalse(result["executor_authorized"])
        self.assertTrue(result["dry_run"])
        self.assertEqual(result["source_sha"], SOURCE_SHA)

    def test_side_effect_requires_approval(self) -> None:
        result = self.contract.decide(
            self.request(side_effect=True),
            allowed_hosts=("example.com",),
        )
        self.assertEqual(result["decision"], AutomationDecision.REQUIRE_APPROVAL.value)
        self.assertFalse(result["executor_authorized"])

    def test_non_allowlisted_host_is_denied(self) -> None:
        result = self.contract.decide(
            self.request(target="https://other.example/docs"),
            allowed_hosts=("example.com",),
        )
        self.assertEqual(result["decision"], AutomationDecision.DENY.value)

    def test_unsafe_scheme_is_denied(self) -> None:
        result = self.contract.decide(
            self.request(target="javascript:alert(1)"),
            allowed_hosts=("example.com",),
        )
        self.assertEqual(result["decision"], AutomationDecision.DENY.value)

    def test_shell_like_target_is_rejected(self) -> None:
        with self.assertRaises(ControlledAutomationError):
            self.contract.decide(
                self.request(target="https://example.com/bash -c whoami"),
                allowed_hosts=("example.com",),
            )

    def test_mcp_target_is_rejected(self) -> None:
        with self.assertRaises(ControlledAutomationError):
            self.contract.decide(
                self.request(target="mcp://server/tool"),
            )

    def test_unknown_capability_is_rejected(self) -> None:
        with self.assertRaises(ControlledAutomationError):
            self.contract.decide(self.request(capability="WRITE_SYSTEM"))

    def test_non_read_action_is_denied(self) -> None:
        result = self.contract.decide(
            self.request(action="delete"),
            allowed_hosts=("example.com",),
        )
        self.assertEqual(result["decision"], AutomationDecision.DENY.value)

    def test_invalid_source_sha_is_rejected(self) -> None:
        with self.assertRaises(ControlledAutomationError):
            self.contract.decide(self.request(source_sha="not-a-sha"))

    def test_decision_fingerprint_is_deterministic(self) -> None:
        first = self.contract.decide(self.request(), allowed_hosts=("example.com",))
        second = self.contract.decide(self.request(), allowed_hosts=("example.com",))
        self.assertEqual(first["decision_fingerprint"], second["decision_fingerprint"])


if __name__ == "__main__":
    unittest.main()
