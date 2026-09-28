"""AEOS temporal freshness boundary.

Freshness is explicit and deterministic. A timestamp is never treated as
current merely because it exists; the caller must supply the verification
clock and a bounded maximum age. Invalid, future, or expired observations are
blocked rather than coerced to PASS.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


class FreshnessError(ValueError):
    """Raised when temporal validity cannot be established."""


@dataclass(frozen=True)
class FreshnessDecision:
    status: str
    age_seconds: int
    max_age_seconds: int
    reference_time: str
    observed_at: str

    @property
    def fresh(self) -> bool:
        return self.status == "FRESH"


def _parse(value: str, name: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise FreshnessError(f"{name} timestamp required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise FreshnessError(f"invalid {name} timestamp") from exc
    if parsed.tzinfo is None:
        raise FreshnessError(f"{name} timestamp must include timezone")
    return parsed.astimezone(timezone.utc)


def evaluate_freshness(
    *,
    observed_at: str,
    reference_time: str,
    max_age_seconds: int,
) -> FreshnessDecision:
    """Evaluate freshness using an explicit, externally supplied clock.

    The function does not read wall-clock time and therefore remains
    deterministic under replay. Future observations are blocked as CONFLICT;
    observations older than the configured bound are STALE.
    """
    if type(max_age_seconds) is not int or max_age_seconds < 0:
        raise FreshnessError("max_age_seconds must be a non-negative integer")
    observed = _parse(observed_at, "observed_at")
    reference = _parse(reference_time, "reference_time")
    delta = reference - observed
    age_seconds = int(delta.total_seconds())
    if age_seconds < 0:
        status = "CONFLICT"
        age_seconds = 0
    elif age_seconds > max_age_seconds:
        status = "STALE"
    else:
        status = "FRESH"
    return FreshnessDecision(
        status=status,
        age_seconds=age_seconds,
        max_age_seconds=max_age_seconds,
        reference_time=reference.isoformat().replace("+00:00", "Z"),
        observed_at=observed.isoformat().replace("+00:00", "Z"),
    )
