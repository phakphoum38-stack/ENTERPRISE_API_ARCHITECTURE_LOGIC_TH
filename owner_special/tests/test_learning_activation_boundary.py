from __future__ import annotations

import unittest

from owner_special.research_os_friend.learning_activation_boundary import (
    LearningActivationError,
    LearningActivationRequest,
    LearningSkillActivator,
)


class _Registry:
    def __init__(self, entry: dict) -> None:
        self._entry = entry

    def snapshot(self) -> dict:
        return {"entries": [dict(self._entry)]}


class _Consumption:
    pass


OWNER = "owner_special"
SOURCE_SHA = "a" * 40
CORRELATION = "corr-h13"
SKILL_FP = "b" * 64


def entry() -> dict:
    return {
        "owner": OWNER,
        "source_sha": SOURCE_SHA,
        "correlation_id": CORRELATION,
        "name": "bounded research skill",
        "goal": "inspect trusted research context",
        "evidence_fingerprint": "c" * 64,
        "promotion_fingerprint": "d" * 64,
        "version": 1,
        "fingerprint": SKILL_FP,
    }


class LearningActivationBoundaryTests(unittest.TestCase):
    def activator(self) -> LearningSkillActivator:
        return LearningSkillActivator(_Registry(entry()), _Consumption())

    def request(self, **overrides) -> LearningActivationRequest:
        values = {
            "owner": OWNER,
            "source_sha": SOURCE_SHA,
            "correlation_id": CORRELATION,
            "skill_fingerprint": SKILL_FP,
        }
        values.update(overrides)
        return LearningActivationRequest(**values)

    def test_inspection_activation_is_allowed_and_read_only(self) -> None:
        result = self.activator().activate(self.request())
        self.assertEqual(result["decision"], "ALLOW_INSPECTION")
        self.assertTrue(result["read_only"])
        self.assertEqual(result["authority"], "none")

    def test_execute_without_approval_requires_approval(self) -> None:
        result = self.activator().activate(
            self.request(intent="execute", h12_decision="REQUIRE_APPROVAL")
        )
        self.assertEqual(result["decision"], "REQUIRE_APPROVAL")
        self.assertTrue(result["read_only"])

    def test_execute_with_approval_only_allows_activation_intent(self) -> None:
        result = self.activator().activate(
            self.request(
                intent="execute",
                h12_decision="REQUIRE_APPROVAL",
                approval_state="APPROVED",
            )
        )
        self.assertEqual(result["decision"], "ALLOW_ACTIVATION")
        self.assertEqual(result["authority"], "none")

    def test_identity_mismatch_fails_closed(self) -> None:
        with self.assertRaises(LearningActivationError):
            self.activator().activate(self.request(source_sha="e" * 40))

    def test_denied_activation_fails_closed(self) -> None:
        with self.assertRaises(LearningActivationError):
            self.activator().activate(
                self.request(
                    intent="execute",
                    h12_decision="DENY",
                    approval_state="DENIED",
                )
            )

    def test_unsafe_skill_payload_is_rejected(self) -> None:
        unsafe = entry()
        unsafe["goal"] = "run shell command"
        with self.assertRaises(LearningActivationError):
            LearningSkillActivator(_Registry(unsafe), _Consumption()).activate(self.request())

    def test_snapshot_is_detached_and_fingerprint_is_deterministic(self) -> None:
        activator = self.activator()
        first = activator.activate(self.request())
        first["skill"]["name"] = "mutated"
        second = activator.activate(self.request())
        self.assertEqual(second["skill"]["name"], "bounded research skill")
        self.assertEqual(
            first["decision_fingerprint"],
            second["decision_fingerprint"],
        )


if __name__ == "__main__":
    unittest.main()
