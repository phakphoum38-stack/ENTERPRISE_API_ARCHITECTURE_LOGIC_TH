"""Tests for the Research OS resource governance foundation."""
from datetime import datetime, timedelta, timezone

import pytest

from resource_governance import (
    Decision,
    Entitlement,
    Limit,
    QuotaDimension,
    QuotaError,
    ResourceGovernance,
    Usage,
    Window,
)


NOW = datetime(2026, 9, 14, 15, 0, tzinfo=timezone.utc)


def entitlement() -> Entitlement:
    return Entitlement(
        tier="developer",
        scopes=frozenset({"chat", "brain"}),
        limits=(
            Limit(QuotaDimension.REQUESTS, Window.DAY, 10),
            Limit(QuotaDimension.TOKENS, Window.DAY, 1_000),
        ),
        priority=10,
        max_concurrency=2,
    )


def test_allows_usage_inside_limits() -> None:
    engine = ResourceGovernance()
    engine.register("user-1", entitlement())
    result = engine.evaluate("user-1", Usage(requests=2, tokens=100), now=NOW)
    assert result.decision is Decision.ALLOW
    assert result.reason == "within_entitlement"


def test_denies_when_window_limit_would_be_exceeded() -> None:
    engine = ResourceGovernance()
    engine.register("user-1", entitlement())
    reservation = engine.reserve("user-1", Usage(requests=8, tokens=800), now=NOW)
    assert reservation.decision is Decision.ALLOW
    blocked = engine.evaluate("user-1", Usage(requests=3), now=NOW)
    assert blocked.decision is Decision.DENY
    assert blocked.reason == "quota_exceeded:requests:day"


def test_reservation_commit_counts_actual_usage() -> None:
    engine = ResourceGovernance()
    engine.register("user-1", entitlement())
    result = engine.reserve("user-1", Usage(requests=5, tokens=500), now=NOW)
    assert result.reservation_id
    engine.commit(result.reservation_id, actual=Usage(requests=3, tokens=250), now=NOW)
    snapshot = engine.snapshot("user-1", now=NOW)
    assert snapshot["requests:day:used"] == 3
    assert snapshot["tokens:day:used"] == 250


def test_release_returns_reserved_capacity() -> None:
    engine = ResourceGovernance()
    engine.register("user-1", entitlement())
    result = engine.reserve("user-1", Usage(requests=10), now=NOW)
    assert result.reservation_id
    engine.release(result.reservation_id)
    assert engine.evaluate("user-1", Usage(requests=10), now=NOW).decision is Decision.ALLOW


def test_concurrency_is_separate_from_request_quota() -> None:
    engine = ResourceGovernance()
    engine.register("user-1", entitlement())
    first = engine.reserve("user-1", Usage(concurrent_jobs=2), now=NOW)
    assert first.decision is Decision.ALLOW
    second = engine.evaluate("user-1", Usage(concurrent_jobs=1), now=NOW)
    assert second.decision is Decision.THROTTLE
    engine.release(first.reservation_id)


def test_expired_reservation_does_not_block_capacity() -> None:
    engine = ResourceGovernance(reservation_ttl=timedelta(minutes=1))
    engine.register("user-1", entitlement())
    result = engine.reserve("user-1", Usage(requests=10), now=NOW)
    assert result.reservation_id
    later = NOW + timedelta(minutes=2)
    assert engine.evaluate("user-1", Usage(requests=10), now=later).decision is Decision.ALLOW


def test_rejects_negative_limit_and_unknown_principal() -> None:
    with pytest.raises(QuotaError):
        Limit(QuotaDimension.REQUESTS, Window.DAY, -1)
    engine = ResourceGovernance()
    with pytest.raises(QuotaError, match="unknown principal"):
        engine.evaluate("missing", Usage(requests=1), now=NOW)
