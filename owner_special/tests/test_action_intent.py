from __future__ import annotations

import unittest

from owner_special.research_os_friend.action_intent import (
    ActionApproval,
    ActionEffect,
    ActionIntent,
    ActionIntentError,
    ActionIntentValidator,
)


SHA = "3ca8108f4586bc05240cb009fe21c8350137d670"


def _intent(**overrides):
    values = {
        "schema": ActionIntent.SCHEMA,
        "version": ActionIntent.VERSION,
        "owner_id": "owner",
        "session_id": "session",
        "intent_id": "intent-1",
        "action_type": "inspect",
        "goal": "Inspect evidence",
        "target": "EV-001",
        "effect": ActionEffect.READ_ONLY,
        "approval": ActionApproval.NOT_REQUIRED,
        "correlation_id": "corr-1",
        "source_sha": SHA,
        "params": (),
    }
    values.update(overrides)
    return ActionIntent(**values)


class ActionIntentTests(unittest.TestCase):
    def test_valid_intent_is_deterministic_and_bounded(self):
        first = _intent()
        second = _intent()
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(first.request_fingerprint, second.request_fingerprint)
        self.assertEqual(len(first.request_fingerprint), 64)

    def test_unsafe_or_unapproved_intent_fails_closed(self):
        cases = (
            ("action_type", "shell"),
            ("action_type", "approve"),
            ("effect", ActionEffect.SIDE_EFFECT),
            ("approval", ActionApproval.REQUIRED),
        )
        for field, value in cases:
            with self.subTest(field=field, value=value):
                with self.assertRaises(ActionIntentError):
                    _intent(**{field: value})

    def test_executable_or_secret_like_content_is_rejected(self):
        cases = (
            ("goal", "run powershell"),
            ("target", "javascript:alert(1)"),
            ("target", "BEGIN PRIVATE KEY"),
            ("params", (("mode", "subprocess"),)),
        )
        for field, value in cases:
            with self.subTest(field=field, value=value):
                with self.assertRaises(ActionIntentError):
                    _intent(**{field: value})

    def test_invalid_source_sha_fails_closed(self):
        with self.assertRaises(ActionIntentError):
            _intent(source_sha="a" * 39)

    def test_duplicate_parameter_names_fail_closed(self):
        with self.assertRaises(ActionIntentError):
            _intent(params=(("limit", "10"), ("limit", "20")))

    def test_validator_is_pure(self):
        intent = _intent()
        self.assertIsNone(ActionIntentValidator.validate(intent))


if __name__ == "__main__":
    unittest.main()
