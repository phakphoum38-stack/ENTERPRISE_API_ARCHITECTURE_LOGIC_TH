from __future__ import annotations

from .brain import BrainCore
from .factory import SoftwareFactory, SoftwareFactoryPlan
from .models import OrchestrationDecision, Workload
from .providers import ProviderRegistry


class UnifiedMasterOrchestrator:
    """Single coordination authority for V3 Clean."""

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
