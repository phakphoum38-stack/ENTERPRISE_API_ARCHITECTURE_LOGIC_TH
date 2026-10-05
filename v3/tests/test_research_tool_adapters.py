from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.research_os_api.adapter_runtime_security import AdapterRuntimeDenied
from research_os_v3.research_tool_adapters import (
    BuiltinResearchTools,
    ToolRequest,
)


class ResearchToolAdapterTests(unittest.TestCase):
    @staticmethod
    def _principal() -> dict[str, object]:
        return {
            "user_id": "user-a",
            "email": "owner@example.com",
            "role": "owner",
            "session_id": "session-a",
            "exp": 4102444800,
        }

    def test_direct_execution_is_fail_closed(self) -> None:
        result = BuiltinResearchTools().execute(
            ToolRequest("python", "analyze", {"source": "value = 1"})
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "AuthorizationRequired")

    def test_file_read_returns_provenance_after_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "note.txt"
            path.write_text("research evidence", encoding="utf-8")
            result, decision = BuiltinResearchTools().execute_authorized(
                ToolRequest("file", "read", {"path": str(path)}),
                principal=self._principal(),
                request_id="req-file-1",
                policy_decision="ALLOW",
            )
            self.assertTrue(decision.allowed)
            self.assertTrue(result.success)
            self.assertEqual(result.data, "research evidence")
            self.assertTrue(result.source_uri.startswith("file://"))

    def test_python_analyze_is_deterministic(self) -> None:
        result, _ = BuiltinResearchTools().execute_authorized(
            ToolRequest("python", "analyze", {"source": "import json\nvalue = 1"}),
            principal=self._principal(),
            request_id="req-python-1",
            policy_decision="ALLOW",
        )
        self.assertTrue(result.success)
        self.assertEqual(result.data["imports"], ["json"])

    def test_shell_is_allowlisted(self) -> None:
        tools = BuiltinResearchTools()
        denied = tools.execute(ToolRequest("shell", "run", {"command": ["rm", "-rf", "/"]}))
        self.assertFalse(denied.success)
        self.assertEqual(denied.error, "CommandNotAllowed")

    def test_unknown_tool_fails_closed(self) -> None:
        result = BuiltinResearchTools().execute(ToolRequest("network", "search", {}))
        self.assertFalse(result.success)
        self.assertEqual(result.error, "ToolNotFound")

    def test_authorized_execution_crosses_security_wall(self) -> None:
        principal = self._principal()
        result, decision = BuiltinResearchTools().execute_authorized(
            ToolRequest("python", "analyze", {"source": "value = 1"}),
            principal=principal,
            request_id="req-runtime-1",
            policy_decision="ALLOW",
        )
        self.assertTrue(result.success)
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.evidence["authorization_result"], "ALLOW")

    def test_unauthorized_execution_never_reaches_adapter(self) -> None:
        principal = {
            "user_id": "user-a",
            "email": "owner@example.com",
            "role": "owner",
            "session_id": "session-a",
            "exp": 4102444800,
        }
        with self.assertRaises(AdapterRuntimeDenied):
            BuiltinResearchTools().execute_authorized(
                ToolRequest("shell", "run", {"command": ["rm", "-rf", "/"]}),
                principal=principal,
                request_id="req-runtime-2",
                policy_decision="ALLOW",
            )


if __name__ == "__main__":
    unittest.main()
