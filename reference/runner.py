from dataclasses import dataclass
from typing import Any, Callable

from reference.execution_loop import ReferenceExecutionLoop, ExecutionResult


@dataclass
class RunnerConfig:
    runner_id: str
    max_jobs_per_cycle: int = 1


class StatelessRunner:
    """Reference stateless runner: state lives in JobStore/queue, not the runner."""

    def __init__(self, loop: ReferenceExecutionLoop, config: RunnerConfig) -> None:
        self.loop = loop
        self.config = config

    def run_once(self, handler: Callable[[dict[str, Any]], Any]) -> ExecutionResult:
        return self.loop.process_once(self.config.runner_id, handler)

    def run_until_empty(self, handler: Callable[[dict[str, Any]], Any]) -> list[ExecutionResult]:
        results: list[ExecutionResult] = []
        for _ in range(self.config.max_jobs_per_cycle):
            try:
                results.append(self.run_once(handler))
            except TimeoutError:
                break
        return results
