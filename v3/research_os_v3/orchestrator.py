from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .brain import BrainCore
from .execution import FactoryExecutionEngine, FactoryExecutionResult, StageHandler
from .factory import SoftwareFactory, SoftwareFactoryPlan
from .models import OrchestrationDecision, Workload
from .providers import ProviderRegistry


class UnifiedMasterOrchestrator:
    """Single coordination authority for V3 Full 10x10."""

    contract = "unified-master-orchestrator-v3"

    def __init__(
        self,
        brain: BrainCore | None = None,
        providers: ProviderRegistry | None = None,
        factory: SoftwareFactory | None = None,
    ) -> None:
        self.brain = brain or BrainCore()
        self.providers = providers or ProviderRegistry()
        self.factory = factory or SoftwareFactory()

    def decide(self, workload: Workload) -> OrchestrationDecision:
        profile, demand, reason = self.brain.select_profile(workload)
        provider = self.providers.select_ready()
        return OrchestrationDecision(
            profile=profile,
            provider=provider.name,
            demand=demand,
            reason=reason,
        )

    def plan(self, workload: Workload) -> tuple[OrchestrationDecision, SoftwareFactoryPlan]:
        decision = self.decide(workload)
        return decision, self.factory.plan(decision.profile)

    def execute_factory(
        self,
        workload: Workload,
        *,
        handlers: Mapping[str, StageHandler],
        release_inputs: Mapping[str, object] | None = None,
        evidence_path: Path | None = None,
        hard_concurrency_limit: int = 64,
    ) -> FactoryExecutionResult:
        decision, plan = self.plan(workload)
        engine = FactoryExecutionEngine(
            hard_concurrency_limit=hard_concurrency_limit,
        )
        return engine.execute(
            workload=workload,
            decision=decision,
            plan=plan,
            handlers=handlers,
            release_inputs=release_inputs,
            evidence_path=evidence_path,
        )
