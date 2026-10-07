"""Unit tests for the Research OS resource governance foundation."""
from datetime import datetime, timedelta, timezone
import os
import unittest
from unittest import mock

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


class ResourceGovernanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pepper = mock.patch.dict(os.environ, {"RESEARCH_OS_API_KEY_PEPPER": "test-pepper"})
        self.pepper.start()
        self.addCleanup(self.pepper.stop)

    def test_allows_usage_inside_limits(self) -> None:
        engine = ResourceGovernance()
        engine.register("user-1", entitlement())
        result = engine.evaluate("user-1", Usage(requests=2, tokens=100), now=NOW)
        self.assertIs(result.decision, Decision.ALLOW)
        self.assertEqual(result.reason, "within_entitlement")

    def test_denies_when_window_limit_would_be_exceeded(self) -> None:
        engine = ResourceGovernance()
        engine.register("user-1", entitlement())
        reservation = engine.reserve("user-1", Usage(requests=8, tokens=800), now=NOW)
        self.assertIs(reservation.decision, Decision.ALLOW)
        blocked = engine.evaluate("user-1", Usage(requests=3), now=NOW)
        self.assertIs(blocked.decision, Decision.DENY)
        self.assertEqual(blocked.reason, "quota_exceeded:requests:day")

    def test_reservation_commit_counts_actual_usage(self) -> None:
        engine = ResourceGovernance()
        engine.register("user-1", entitlement())
        result = engine.reserve("user-1", Usage(requests=5, tokens=500), now=NOW)
        self.assertTrue(result.reservation_id)
        engine.commit(result.reservation_id, actual=Usage(requests=3, tokens=250), now=NOW)
        snapshot = engine.snapshot("user-1", now=NOW)
        self.assertEqual(snapshot["requests:day:used"], 3)
        self.assertEqual(snapshot["tokens:day:used"], 250)

    def test_release_returns_reserved_capacity(self) -> None:
        engine = ResourceGovernance()
        engine.register("user-1", entitlement())
        result = engine.reserve("user-1", Usage(requests=10), now=NOW)
        self.assertTrue(result.reservation_id)
        engine.release(result.reservation_id)
        self.assertIs(engine.evaluate("user-1", Usage(requests=10), now=NOW).decision, Decision.ALLOW)

    def test_concurrency_is_separate_from_request_quota(self) -> None:
        engine = ResourceGovernance()
        engine.register("user-1", entitlement())
        first = engine.reserve("user-1", Usage(concurrent_jobs=2), now=NOW)
        self.assertIs(first.decision, Decision.ALLOW)
        second = engine.evaluate("user-1", Usage(concurrent_jobs=1), now=NOW)
        self.assertIs(second.decision, Decision.THROTTLE)
        engine.release(first.reservation_id)

    def test_expired_reservation_does_not_block_capacity(self) -> None:
        engine = ResourceGovernance(reservation_ttl=timedelta(minutes=1))
        engine.register("user-1", entitlement())
        result = engine.reserve("user-1", Usage(requests=10), now=NOW)
        self.assertTrue(result.reservation_id)
        later = NOW + timedelta(minutes=2)
        self.assertIs(engine.evaluate("user-1", Usage(requests=10), now=later).decision, Decision.ALLOW)

    def test_rejects_negative_limit_and_unknown_principal(self) -> None:
        with self.assertRaises(QuotaError):
            Limit(QuotaDimension.REQUESTS, Window.DAY, -1)
        engine = ResourceGovernance()
        with self.assertRaisesRegex(QuotaError, "unknown principal"):
            engine.evaluate("missing", Usage(requests=1), now=NOW)
