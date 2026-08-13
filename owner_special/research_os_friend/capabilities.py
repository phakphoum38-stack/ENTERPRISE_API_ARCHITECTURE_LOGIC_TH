from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Capability:
    name: str
    layer: str
    description: str
    owner_managed: bool = True


class CapabilityRegistry:
    def __init__(self) -> None:
        self._items: dict[str, Capability] = {}

    def register(self, capability: Capability) -> None:
        if not capability.name or capability.name in self._items:
            raise ValueError(f"duplicate or empty capability: {capability.name}")
        self._items[capability.name] = capability

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._items))

    def snapshot(self) -> tuple[dict[str, object], ...]:
        return tuple(asdict(self._items[name]) for name in self.names())


def install_friend_complete_capabilities() -> CapabilityRegistry:
    registry = CapabilityRegistry()
    capabilities = (
        Capability("identity", "boundary", "Owner identity and owner-only authorization."),
        Capability("brain", "intelligence", "Adaptive 1^3, 3^3, 6^3 and 6^6 logical capacity selection."),
        Capability("reasoning-summary", "intelligence", "High-level decision plan and rationale summaries."),
        Capability("skills", "capability", "Owner-managed skill catalog and dispatch."),
        Capability("memory", "context", "Owner/profile/session scoped memory."),
        Capability("persistent-memory", "context", "Atomic local persistence for scoped owner memory."),
        Capability("context", "context", "Scoped context assembly before provider execution."),
        Capability("policy", "boundary", "Owner and tool permission enforcement."),
        Capability("tools", "capability", "Permission-checked tool registry."),
        Capability("providers", "intelligence", "Provider adapter and routing boundary."),
        Capability("v3-bridge", "integration", "Bridge to Research OS V3 Brain, Factory, Provider and storage contracts."),
        Capability("orchestrator", "control", "Composition root coordinating all Friend components."),
        Capability("factory", "execution", "Software-factory execution contract inherited through the V3 bridge."),
        Capability("evidence", "quality", "Credential-redacted evidence and audit records."),
        Capability("owner-bundle", "portability", "Secret-free portable owner architecture bundle."),
        Capability("tests", "quality", "Cross-platform unit and smoke certification."),
    )
    for capability in capabilities:
        registry.register(capability)
    return registry
