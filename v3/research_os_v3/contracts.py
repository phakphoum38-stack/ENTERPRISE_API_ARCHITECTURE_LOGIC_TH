from __future__ import annotations

from .models import OrchestrationDecision
from .orchestrator import UnifiedMasterOrchestrator
from .providers import ProviderRegistry


def health_contract() -> dict[str, object]:
    return {"status": "ok", "version": "v3-clean"}


def master_contract(decision: OrchestrationDecision) -> dict[str, object]:
    return {
        "contract": UnifiedMasterOrchestrator.contract,
        "scale": decision.profile.tier.value,
        "fanout": decision.profile.fanout,
        "depth": decision.profile.depth,
        "maximum_leaf_capacity": decision.profile.capacity,
        "demand": decision.demand,
        "provider": decision.provider,
        "reason": decision.reason,
    }


def providers_contract(registry: ProviderRegistry) -> dict[str, object]:
    return {"providers": [status.to_safe_dict() for status in registry.statuses()]}
