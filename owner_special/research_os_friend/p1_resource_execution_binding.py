"""P1-03 bind the existing ResourceControlPlane result to canonical execution identity."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from typing import Any
from .canonical_identity_federation import CanonicalIdentity, CanonicalIdentityError
from .resource_admission_binding import ResourceAdmissionBinding, bind_resource_admission, assert_admission_lineage

class P1ResourceBindingError(CanonicalIdentityError):
    """Raised when a resource execution result cannot be bound safely."""

@dataclass(frozen=True)
class ResourceExecutionBinding:
    resource: ResourceAdmissionBinding
    status: str
    provider: str | None
    model: str | None
    ledger_hash: str | None
    evidence_hash: str | None

    @property
    def binding_hash(self) -> str:
        material = {"resource_binding": self.resource.binding_hash, "status": self.status, "provider": self.provider, "model": self.model, "ledger_hash": self.ledger_hash, "evidence_hash": self.evidence_hash}
        return hashlib.sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def bind_resource_execution(*, identity: CanonicalIdentity, execution_result: Any) -> ResourceExecutionBinding:
    """Bind an existing resource ExecutionResult; denied/unreserved results fail closed."""
    admission = getattr(execution_result, "admission", None)
    request_id = getattr(execution_result, "request_id", None)
    if admission is None or not isinstance(request_id, str) or not request_id.strip():
        raise P1ResourceBindingError("execution result lacks resource admission identity")
    admission_id = getattr(admission, "reservation_id", None)
    principal_id = getattr(admission, "principal_id", None)
    if not isinstance(admission_id, str) or not admission_id.strip():
        raise P1ResourceBindingError("execution result has no admitted reservation")
    if not isinstance(principal_id, str) or not principal_id.strip():
        raise P1ResourceBindingError("execution result lacks principal identity")
    provider = getattr(execution_result, "provider", None)
    model = getattr(execution_result, "model", None)
    resource = bind_resource_admission(identity=identity, request_id=request_id, admission_id=admission_id, principal_id=principal_id, provider=provider, model=model)
    assert_admission_lineage(resource, identity)
    ledger = getattr(execution_result, "ledger_entry", None)
    evidence = getattr(execution_result, "evidence", None)
    ledger_hash = getattr(ledger, "entry_hash", None)
    evidence_hash = evidence.get("evidence_hash") if isinstance(evidence, dict) else None
    for name, value in (("ledger_hash", ledger_hash), ("evidence_hash", evidence_hash)):
        if value is not None and (not isinstance(value, str) or len(value) != 64):
            raise P1ResourceBindingError(f"{name} must be a SHA-256 hex digest")
    status = getattr(getattr(admission, "decision", None), "value", None) or "unknown"
    return ResourceExecutionBinding(resource, status, provider, model, ledger_hash, evidence_hash)
