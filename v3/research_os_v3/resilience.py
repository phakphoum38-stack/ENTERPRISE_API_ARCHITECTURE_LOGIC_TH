from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar


T = TypeVar("T")


class CircuitOpenError(RuntimeError):
    pass


class ProviderUnavailableError(RuntimeError):
    pass


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    initial_backoff_seconds: float = 0.25
    max_backoff_seconds: float = 2.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.initial_backoff_seconds < 0 or self.max_backoff_seconds < 0:
            raise ValueError("retry backoff must be non-negative")

    def delay_for_retry(self, retry_number: int) -> float:
        if retry_number < 1:
            return 0.0
        delay = self.initial_backoff_seconds * (2 ** (retry_number - 1))
        return min(delay, self.max_backoff_seconds)


@dataclass(frozen=True)
class CircuitBreakerPolicy:
    failure_threshold: int = 3
    recovery_timeout_seconds: float = 30.0

    def __post_init__(self) -> None:
        if self.failure_threshold < 1:
            raise ValueError("failure_threshold must be at least 1")
        if self.recovery_timeout_seconds < 0:
            raise ValueError("recovery_timeout_seconds must be non-negative")


class CircuitBreaker:
    def __init__(
        self,
        policy: CircuitBreakerPolicy,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.policy = policy
        self._clock = clock
        self._failures = 0
        self._opened_at: float | None = None
        self._lock = threading.Lock()

    @property
    def failures(self) -> int:
        with self._lock:
            return self._failures

    def state(self) -> str:
        with self._lock:
            return self._state_locked()

    def allow_request(self) -> bool:
        with self._lock:
            return self._state_locked() != "open"

    def record_success(self) -> None:
        with self._lock:
            self._failures = 0
            self._opened_at = None

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1
            if self._failures >= self.policy.failure_threshold:
                self._opened_at = self._clock()

    def _state_locked(self) -> str:
        if self._opened_at is None:
            return "closed"
        if self._clock() - self._opened_at >= self.policy.recovery_timeout_seconds:
            return "half-open"
        return "open"


class ResilientInvoker:
    def __init__(
        self,
        *,
        retry_policy: RetryPolicy | None = None,
        circuit_policy: CircuitBreakerPolicy | None = None,
        sleeper: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.retry_policy = retry_policy or RetryPolicy()
        self.breaker = CircuitBreaker(circuit_policy or CircuitBreakerPolicy(), clock=clock)
        self._sleeper = sleeper

    @property
    def circuit_state(self) -> str:
        return self.breaker.state()

    def invoke(self, operation: Callable[[], T]) -> T:
        if not self.breaker.allow_request():
            raise CircuitOpenError("provider circuit is open")

        last_error: Exception | None = None
        for attempt in range(1, self.retry_policy.max_attempts + 1):
            try:
                result = operation()
            except Exception as exc:
                last_error = exc
                if attempt < self.retry_policy.max_attempts:
                    delay = self.retry_policy.delay_for_retry(attempt)
                    if delay > 0:
                        self._sleeper(delay)
                continue
            self.breaker.record_success()
            return result

        self.breaker.record_failure()
        raise ProviderUnavailableError(
            f"provider invocation failed after {self.retry_policy.max_attempts} attempt(s)"
        ) from last_error
