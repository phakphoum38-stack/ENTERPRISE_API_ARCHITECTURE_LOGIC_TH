from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class RepairAttempt(Generic[T]):
    attempt: int
    success: bool
    result: T | None = None
    error: str | None = None


@dataclass(frozen=True)
class RepairOutcome(Generic[T]):
    success: bool
    attempts: tuple[RepairAttempt[T], ...]

    @property
    def result(self) -> T | None:
        for attempt in reversed(self.attempts):
            if attempt.success:
                return attempt.result
        return None


class RetryRepairLoop:
    """Bounded retry loop with an explicit repair hook between attempts."""

    def __init__(self, max_attempts: int = 3) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        self.max_attempts = max_attempts

    def run(
        self,
        execute: Callable[[], T],
        repair: Callable[[Exception, int], None],
    ) -> RepairOutcome[T]:
        attempts: list[RepairAttempt[T]] = []
        for number in range(1, self.max_attempts + 1):
            try:
                result = execute()
                attempts.append(RepairAttempt(number, True, result=result))
                return RepairOutcome(True, tuple(attempts))
            except Exception as exc:  # boundary intentionally captures task failures
                attempts.append(RepairAttempt(number, False, error=f"{type(exc).__name__}: {exc}"))
                if number < self.max_attempts:
                    repair(exc, number)
        return RepairOutcome(False, tuple(attempts))
