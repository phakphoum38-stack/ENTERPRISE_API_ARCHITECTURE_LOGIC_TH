from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .brain import BrainCore
from .execution import FactoryExecutionEngine, FactoryExecutionResult, StageHandler
from .factory import SoftwareFactory, SoftwareFactoryPlan
from .models import OrchestrationDecision, Workload
from .providers import CompletionRequest, CompletionResponse, ProviderRegistry


class UnifiedMasterOrchestrator:
    """Single coordination authority for Research OS V3.

    Scale selection is logical and lazy; real execution remains bounded by the
    execution engine. Provider-backed answers flow through this master so chat,
    local memory context, and provider selection keep one coordination path.
    """

    contract = "unified-master-orchestrator-v3-clean"

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

    def answer(
        self,
        prompt: str,
        *,
        memory_context: str | None = None,
        preferred_provider: str | None = None,
        system_prompt: str | None = None,
    ) -> CompletionResponse:
        cleaned = prompt.strip()
        if not cleaned:
            raise ValueError("prompt must not be empty")

        governed_system = (
            "You are Research OS V3. The Unified Master is the single coordination authority. "
            "Use provided local memory only as relevant context, keep user/profile isolation, "
            "never expose secrets, and never claim an action ran unless an execution result is supplied."
        )
        if system_prompt:
            governed_system += f"\n\nRequested conversation guidance:\n{system_prompt.strip()}"
        if memory_context:
            governed_system += f"\n\nRelevant local memory/context:\n{memory_context}"

        return self.providers.complete(
            CompletionRequest(prompt=cleaned, system_prompt=governed_system),
            preferred=preferred_provider,
        )

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
