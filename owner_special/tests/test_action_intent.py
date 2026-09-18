from __future__ import annotations

import pytest

from owner_special.research_os_friend.action_intent import (
    ActionApproval,
    ActionEffect,
    ActionIntent,
    ActionIntentError,
    ActionIntentValidator,
)


SHA = "5e16741bb42f6f888542d74b37781e723a7d6643"


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


def test_valid_intent_is_deterministic_and_bounded():
    first = _intent()
    second = _intent()
    assert first.to_dict() == second.to_dict()
    assert first.request_fingerprint == second.request_fingerprint
    assert len(first.request_fingerprint) == 64


@pytest.mark.parametrize(
    "field,value",
    [
        ("action_type", "shell"),
        ("action_type", "approve"),
        ("effect", ActionEffect.SIDE_EFFECT),
        ("approval", ActionApproval.REQUIRED),
    ],
)
def test_unsafe_or_unapproved_intent_fails_closed(field, value):
    with pytest.raises(ActionIntentError):
        _intent(**{field: value})


@pytest.mark.parametrize(
    "field,value",
    [
        ("goal", "run powershell"),
        ("target", "javascript:alert(1)"),
        ("target", "BEGIN PRIVATE KEY"),
        ("params", (("mode", "subprocess"),)),
    ],
)
def test_executable_or_secret_like_content_is_rejected(field, value):
    with pytest.raises(ActionIntentError):
        _intent(**{field: value})


def test_invalid_source_sha_fails_closed():
    with pytest.raises(ActionIntentError):
        _intent(source_sha="a" * 39)


def test_duplicate_parameter_names_fail_closed():
    with pytest.raises(ActionIntentError):
        _intent(params=(("limit", "10"), ("limit", "20")))


def test_validator_is_pure():
    intent = _intent()
    assert ActionIntentValidator.validate(intent) is None
