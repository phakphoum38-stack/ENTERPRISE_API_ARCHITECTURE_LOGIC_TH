from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

import ai_gateway


class AIGatewayCompatibilityTests(unittest.TestCase):
    def test_gateway_report_delegates_to_canonical_readiness_owner(self) -> None:
        sentinel = {"active": "mock", "providers": [], "safe": True}
        with patch.object(ai_gateway, "inspect_all", return_value=sentinel) as inspect_all:
            report = ai_gateway.gateway_report()

        self.assertIs(report, sentinel)
        inspect_all.assert_called_once_with()

    def test_gateway_report_does_not_expose_configured_provider_secret(self) -> None:
        secret = "sk-test-gateway-secret-must-not-escape"
        with patch.dict(
            os.environ,
            {
                "RESEARCH_OS_PROVIDER": "openai-responses",
                "OPENAI_API_KEY": secret,
            },
            clear=False,
        ):
            report = ai_gateway.gateway_report()

        serialized = json.dumps(report, sort_keys=True)
        self.assertEqual(report["active"], "openai-responses")
        self.assertTrue(report["safe"])
        self.assertNotIn(secret, serialized)
        openai = next(
            item for item in report["providers"] if item["provider"] == "openai-responses"
        )
        self.assertTrue(openai["ready"])


if __name__ == "__main__":
    unittest.main()
