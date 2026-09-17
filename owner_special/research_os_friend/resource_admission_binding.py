"""P0-6 adapter: bind resource admission to canonical execution identity."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from .canonical_identity_federation import CanonicalIdentity, CanonicalIdentityError

class ResourceAdmissionBindingError(CanonicalIdentityError):
    """Raised when admission identity cannot be bound safely."""

@dataclass(frozen=True)
class ResourceAdmissionBinding:
    request_id: str
    admission_id: str
    principal_id: str
    canonical: CanonicalIdentity
    provider: str | None = None
    model: str | None = None

    def __post_init__(self) -> None:
        for name, value in (("request_id", self.request_id), ("admission_id", self.admission_id), ("principal_id", self.principal_id)):
            if not isinstance(value, str) or not value.strip():
                raise ResourceAdmissionBindingError(f"{name} is required")

    @property
    def binding_material(self) -> dict[str, object]:
        return {"request_id": self.request_id, "admission_id": self.admission_id, "principal_id": self.principal_id, "mission_id": self.canonical.mission_id, "work_id": self.canonical.work_id, "baseline_sha": self.canonical.baseline_sha, "task_id": self.canonical.task_id, "run_id": self.canonical.run_id, "attempt_id": self.canonical.attempt_id, "provider": self.provider, "model": self.model}

    @property
    def binding_hash(self) -> str:
        return hashlib.sha256(json.dumps(self.binding_material, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def bind_resource_admission(*, identity: CanonicalIdentity, request_id: str, admission_id: str, principal_id: str, provider: str | None = None, model: str | None = None) -> ResourceAdmissionBinding:
    return ResourceAdmissionBinding(request_id=request_id.strip(), admission_id=admission_id.strip(), principal_id=principal_id.strip(), canonical=identity, provider=provider.strip() if isinstance(provider, str) and provider.strip() else None, model=model.strip() if isinstance(model, str) and model.strip() else None)

def assert_admission_lineage(binding: ResourceAdmissionBinding, identity: CanonicalIdentity) -> None:
    if binding.canonical.mission_id != identity.mission_id or binding.canonical.work_id != identity.work_id or binding.canonical.baseline_sha != identity.baseline_sha:
        raise ResourceAdmissionBindingError("resource admission lineage does not match canonical identity")
    if binding.canonical.task_id != identity.task_id or binding.canonical.run_id != identity.run_id or binding.canonical.attempt_id != identity.attempt_id:
        raise ResourceAdmissionBindingError("resource admission execution identity does not match canonical identity")
