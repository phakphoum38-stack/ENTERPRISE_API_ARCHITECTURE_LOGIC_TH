from __future__ import annotations

import unittest
from unittest.mock import patch

from adapter_runtime_security import AdapterRuntimeDenied, AdapterRuntimeSecurityBoundary


class AdapterRuntimeSecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gate = AdapterRuntimeSecurityBoundary()
        self.principal = {
            "user_id": "user-a",
            "email": "owner@example.com",
            "role": "owner",
            "session_id": "session-a",
            "iat": 100,
            "exp": 200,
        }

    def authorize(self, **overrides):
        values = {
            "principal": self.principal,
            "session_token": "verified-session-token",
            "capability": "python.analyze",
            "requested_tools": ("python",),
            "arguments": {"source": "value = 1"},
            "request_id": "req-1",
            "policy_decision": "ALLOW",
            "now": 150,
        }
        values.update(overrides)
        with patch("adapter_runtime_security.verify_session", return_value=self.principal):
            return self.gate.authorize(**values)

    def test_valid_request_crosses_boundary(self) -> None:
        decision = self.authorize()
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.adapter, "python")
        self.assertEqual(decision.evidence["authorization_result"], "ALLOW")

    def test_invalid_token_denied(self) -> None:
        with patch("adapter_runtime_security.verify_session", side_effect=ValueError("invalid research session")):
            decision = self.authorize()
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "invalid_or_revoked_session")

    def test_missing_session_denied(self) -> None:
        principal = dict(self.principal)
        principal.pop("session_id")
        decision = self.authorize(principal=principal)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "missing_verified_session")

    def test_expired_session_denied(self) -> None:
        decision = self.authorize(now=201)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "session_expired")

    def test_unknown_capability_denied(self) -> None:
        decision = self.authorize(capability="admin.execute", requested_tools=("admin",))
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "unknown_capability")

    def test_client_adapter_substitution_denied(self) -> None:
        decision = self.authorize(capability="python.analyze", requested_tools=("shell",))
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "capability_not_explicitly_requested")

    def test_policy_must_allow(self) -> None:
        decision = self.authorize(policy_decision="UNKNOWN")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "policy_not_allow")

    def test_path_traversal_denied(self) -> None:
        decision = self.authorize(capability="file.read", requested_tools=("file",), arguments={"path": "../secret.txt"})
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "path_traversal")

    def test_shell_is_allowlisted(self) -> None:
        denied = self.authorize(capability="shell.run", requested_tools=("shell",), arguments={"command": ["rm", "-rf", "/"]})
        self.assertFalse(denied.allowed)
        self.assertEqual(denied.reason, "shell_command_not_allowlisted")

    def test_enforce_raises_on_denial(self) -> None:
        with patch("adapter_runtime_security.verify_session", return_value=self.principal):
            with self.assertRaises(AdapterRuntimeDenied):
                self.gate.enforce(
                    principal=self.principal,
                    session_token="verified-session-token",
                    capability="python.analyze",
                    requested_tools=("python",),
                    arguments={"source": "x"},
                    request_id="req-1",
                    policy_decision="DENY",
                    now=150,
                )


if __name__ == "__main__":
    unittest.main()
