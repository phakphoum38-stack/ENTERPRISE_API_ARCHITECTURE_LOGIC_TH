# P1-05 AEOS Verification Projection

## Purpose
Project the existing execution/evidence binding into the existing AEOS WorkItem
verification boundary without creating a second verification engine or
mutating the work graph.

## Flow
CanonicalIdentity -> ResourceExecutionBinding -> ExecutionEvidenceBinding ->
AEOSVerificationProjection -> existing AEOS verification/certification path

## Safety
The adapter is read-only. It does not transition WorkItem, create leases,
schedule or execute work, grant authority, approve, merge, or modify Git.
Cross-lineage work, baseline drift, and terminal work items fail closed.

The existing AEOS WorkGraph remains the lifecycle authority.
