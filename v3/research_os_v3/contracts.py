from __future__ import annotations

from .models import SCALE_PROFILES, OrchestrationDecision
from .orchestrator import UnifiedMasterOrchestrator
from .providers import ProviderRegistry


def health_contract() -> dict[str, object]:
    maximum = SCALE_PROFILES[-1]
    return {
        "status": "ok",
        "version": "v3.2-unified-full-10x10",
        "maximum_scale": maximum.tier.value,
        "maximum_logical_capacity": maximum.capacity,
        "capacity_policy": "lazy-bounded-execution",
        "authority_contract": UnifiedMasterOrchestrator.contract,
    }


def master_contract(decision: OrchestrationDecision) -> dict[str, object]:
    maximum = SCALE_PROFILES[-1]
    return {
        "contract": "unified-master-orchestrator-v3-clean",
        "authority_contract": UnifiedMasterOrchestrator.contract,
        "scale": decision.profile.tier.value,
        "fanout": decision.profile.fanout,
        "depth": decision.profile.depth,
        "maximum_leaf_capacity": decision.profile.capacity,
        "system_maximum_scale": maximum.tier.value,
        "system_maximum_logical_capacity": maximum.capacity,
        "demand": decision.demand,
        "provider": decision.provider,
        "reason": decision.reason,
    }


def providers_contract(registry: ProviderRegistry) -> dict[str, object]:
    return {"providers": [status.to_safe_dict() for status in registry.statuses()]}
