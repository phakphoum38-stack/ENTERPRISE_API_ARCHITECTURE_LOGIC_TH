from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
import os
import unittest
from unittest.mock import patch

from owner_special.research_os_friend.resource_control_runtime import _measure_friend, install_friend_resource_control
from owner_special.research_os_friend.models import FriendResponse, FriendDecision, ScaleProfile
from tools.research_os_api.execution_contract import MeasuredExecution
from tools.research_os_api.resource_governance import Usage


@dataclass
class _Provider:
    name: str = "owner-mock"


@dataclass
class _Providers:
    names_value: tuple[str, ...] = ("owner-mock",)

    def names(self) -> tuple[str, ...]:
        return self.names_value


@dataclass
class _Owner:
    owner_id: str = "owner"


@dataclass
class _Orchestrator:
    providers: _Providers = field(default_factory=_Providers)
    calls: int = 0

    def handle(self, request):
        self.calls += 1
        return FriendResponse(
            text="ok",
            decision=FriendDecision(ScaleProfile.ONE_CUBED, (), (), (), "ok"),
            provider="owner-mock",
            memory_items=0,
            evidence_id="ev-1",
        )


@dataclass
class _Runtime:
    owner: _Owner = field(default_factory=_Owner)
    orchestrator: _Orchestrator = field(default_factory=_Orchestrator)


class ResourceControlRuntimeTests(unittest.TestCase):
    def test_mock_provider_is_measured_as_exact_zero_cost(self):
        response = FriendResponse(
            text="ok",
            decision=FriendDecision(ScaleProfile.ONE_CUBED, (), (), (), "ok"),
            provider="owner-mock",
            memory_items=0,
            evidence_id="ev-1",
        )
        measured = _measure_friend({"response": response}, {"provider": "owner-mock"})
        self.assertIsInstance(measured, MeasuredExecution)
        self.assertEqual(measured.usage, Usage(requests=1))
        self.assertEqual(measured.cost, Decimal("0"))

    def test_real_provider_without_authoritative_metering_fails_closed(self):
        response = FriendResponse(
            text="ok",
            decision=FriendDecision(ScaleProfile.ONE_CUBED, (), (), (), "ok"),
            provider="openai-compatible",
            memory_items=0,
            evidence_id="ev-1",
        )
        with self.assertRaisesRegex(ValueError, "authoritative Friend provider usage/cost"):
            _measure_friend({"response": response}, {"provider": "openai-compatible"})

    def test_resource_control_patch_is_idempotent(self):
        install_friend_resource_control()
        install_friend_resource_control()
        from owner_special.research_os_friend.runtime import FriendRuntime
        self.assertTrue(FriendRuntime._resource_control_installed)


if __name__ == "__main__":
    unittest.main()
