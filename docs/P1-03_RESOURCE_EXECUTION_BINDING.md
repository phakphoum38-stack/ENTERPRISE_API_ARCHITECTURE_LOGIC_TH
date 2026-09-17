# P1-03 Resource Control Plane → Canonical Execution Binding

Status: experimental, branch-only.

This slice correlates the existing ResourceControlPlane ExecutionResult with
the P0 canonical execution identity.

Existing authority remains unchanged:
- ResourceControlPlane owns admission, reservation, routing, accounting, and resource evidence.
- ResourceAdmissionBinding owns request/admission/principal correlation.
- P0 CanonicalIdentity owns mission/work/baseline/task/run/attempt identity.
- This adapter owns only the immutable cross-plane projection.

A denied/unreserved result cannot be promoted into an execution binding.
Ledger/evidence hashes are preserved as references and validated as SHA-256
digests when present.

No new quota, admission, scheduler, queue, worker, evidence engine,
authorization, verification, or merge path is introduced.
