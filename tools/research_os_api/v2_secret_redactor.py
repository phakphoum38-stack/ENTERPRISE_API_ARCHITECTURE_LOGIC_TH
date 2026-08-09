#!/usr/bin/env python3
"""Secret-aware sanitization for Research OS AI Brain external boundaries.

Phase 4 extends the existing key-based redaction with ephemeral value-aware
scrubbing. Secret values are discovered from sensitive input fields or supplied
explicitly for one execution request, used only in memory while the request is
running, and never written to checkpoints, activity logs or diagnostics.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from v2_brain_core import SENSITIVE_KEY_RE, redact_sensitive


SECRET_REDACTION_CONTRACT = "brain-secret-redaction-phase-4"
_REDACTED = "[REDACTED]"

# Common credential shapes are scrubbed even when an adapter returns them under
# an innocent-looking key such as ``message`` or embeds them in an exception.
_PATTERN_RULES: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}"),
)


def _iter_secret_strings(value: Any, *, key: str | None = None) -> Iterable[str]:
    if key and SENSITIVE_KEY_RE.search(key):
        if isinstance(value, str) and value:
            yield value
        elif isinstance(value, (bytes, bytearray)) and value:
            try:
                decoded = bytes(value).decode("utf-8")
            except UnicodeDecodeError:
                decoded = ""
            if decoded:
                yield decoded
        return
    if isinstance(value, Mapping):
        for child_key, child_value in value.items():
            yield from _iter_secret_strings(child_value, key=str(child_key))
    elif isinstance(value, (list, tuple, set)):
        for child in value:
            yield from _iter_secret_strings(child)


def discover_secret_values(*values: Any, explicit: Iterable[str] = ()) -> tuple[str, ...]:
    """Return deduplicated ephemeral secret values found in sensitive fields.

    Values shorter than four characters are ignored to avoid over-redacting
    ordinary text. The returned values are intended for in-memory use only.
    """

    found: list[str] = []
    for item in explicit:
        text = str(item)
        if len(text) >= 4 and text not in found:
            found.append(text)
    for value in values:
        for secret in _iter_secret_strings(value):
            if len(secret) >= 4 and secret not in found:
                found.append(secret)
    return tuple(found)


def _sanitize_string(text: str, secret_values: Iterable[str]) -> str:
    safe = text
    # Longest values first prevents a short secret prefix from leaving a suffix.
    for secret in sorted({item for item in secret_values if len(item) >= 4}, key=len, reverse=True):
        safe = safe.replace(secret, _REDACTED)
    for pattern in _PATTERN_RULES:
        safe = pattern.sub(_REDACTED, safe)
    return safe


def sanitize_external(value: Any, *, secret_values: Iterable[str] = (), key: str | None = None) -> Any:
    """Sanitize untrusted adapter output/errors before persistence or return."""

    if key and SENSITIVE_KEY_RE.search(key):
        return _REDACTED
    if isinstance(value, Mapping):
        return {
            str(child_key): sanitize_external(
                child_value,
                secret_values=secret_values,
                key=str(child_key),
            )
            for child_key, child_value in value.items()
        }
    if isinstance(value, list):
        return [sanitize_external(item, secret_values=secret_values) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_external(item, secret_values=secret_values) for item in value)
    if isinstance(value, set):
        return [sanitize_external(item, secret_values=secret_values) for item in value]
    if isinstance(value, str):
        return _sanitize_string(value, secret_values)
    return value


@dataclass(frozen=True)
class SanitizedException:
    error_type: str
    message: str


def sanitize_exception(exc: BaseException, *, secret_values: Iterable[str] = ()) -> SanitizedException:
    return SanitizedException(
        error_type=type(exc).__name__,
        message=_sanitize_string(str(exc), secret_values),
    )


def sanitize_request_fields(value: Any, *, secret_values: Iterable[str] = ()) -> Any:
    """Apply both legacy key redaction and Phase 4 value-aware scrubbing."""

    return sanitize_external(redact_sensitive(value), secret_values=secret_values)


def redaction_status() -> dict[str, Any]:
    return {
        "contract": SECRET_REDACTION_CONTRACT,
        "key_based": True,
        "value_aware": True,
        "credential_patterns": len(_PATTERN_RULES),
        "secret_values_persisted": False,
        "scope": "external_output_error_checkpoint_ledger",
    }
