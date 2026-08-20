from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable


@dataclass(frozen=True)
class GateResult:
    name: str
    success: bool
    detail: str = ""


class FinalIntegrationGate:
    """Runs required release checks in order and fails closed on any failed gate."""

    def __init__(self, checks: Iterable[tuple[str, Callable[[], Any]]]) -> None:
        self.checks = tuple(checks)

    def run(self) -> tuple[GateResult, ...]:
        results: list[GateResult] = []
        for name, check in self.checks:
            try:
                value = check()
                success = value is True or (hasattr(value, "success") and bool(value.success))
                detail = "passed" if success else "check returned failure"
            except Exception as exc:  # gate must report, not hide, failures
                success = False
                detail = f"{type(exc).__name__}: {exc}"
            results.append(GateResult(name, success, detail))
        return tuple(results)

    @staticmethod
    def passed(results: Iterable[GateResult]) -> bool:
        return all(result.success for result in results)
