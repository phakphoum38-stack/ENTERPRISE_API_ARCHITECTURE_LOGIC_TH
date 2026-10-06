"""Regression tests for the resource import boundary and central variables."""

from __future__ import annotations

import subprocess
import sys
import unittest
from datetime import timedelta
from pathlib import Path

from tools.research_os_api.admission import ResourceAdmissionGate
from tools.research_os_api.budgets import BudgetLedger
from tools.research_os_api.policy import PolicyEngine
from tools.research_os_api.resource_governance import ResourceGovernance
from tools.research_os_api.resource_runtime_variables import (
    RESOURCE_API_KEY_PREFIX,
    RESOURCE_DEFAULT_CURRENCY,
    RESOURCE_NAMESPACE,
    RESOURCE_RESERVATION_TTL,
    RESOURCE_RUNTIME,
)


class ResourceRuntimeBoundaryTests(unittest.TestCase):
    def test_central_resource_variables_are_stable(self) -> None:
        self.assertEqual(RESOURCE_NAMESPACE, "/platform/v1")
        self.assertEqual(RESOURCE_DEFAULT_CURRENCY, "USD")
        self.assertEqual(RESOURCE_API_KEY_PREFIX, "ro_live_")
        self.assertEqual(RESOURCE_RESERVATION_TTL, timedelta(minutes=5))
        self.assertEqual(RESOURCE_RUNTIME.reservation_ttl_seconds, 300)

    def test_governance_and_admission_share_central_ttl(self) -> None:
        governance = ResourceGovernance()
        admission = ResourceAdmissionGate(governance, PolicyEngine(), BudgetLedger())
        self.assertEqual(governance._reservation_ttl, RESOURCE_RESERVATION_TTL)
        self.assertEqual(admission._reservation_ttl, RESOURCE_RESERVATION_TTL)

    def test_flat_import_compatibility_remains_supported(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        code = """
import sys
sys.path.insert(0, "tools/research_os_api")
import admission
import budgets
import policy
import controlled_router
import resource_governance
import resource_runtime_variables
assert admission.ResourceAdmissionGate
assert budgets.BudgetLedger
assert policy.PolicyEngine
assert controlled_router.GovernedAgentRouter
assert resource_governance.ResourceGovernance
assert resource_runtime_variables.RESOURCE_RUNTIME
"""
        completed = subprocess.run(
            [sys.executable, "-c", code],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            completed.returncode,
            0,
            msg=f"flat import boundary failed:\nSTDOUT={completed.stdout}\nSTDERR={completed.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
