# P0-4 RECON RepairSet → AEOS WorkItem

P0-4 closes the repair-plane bridge without introducing another execution model.

```text
RECON Failure
   ↓
Root Cause
   ↓
RepairSet
   ↓
P0-4 adapter
   ↓
existing AEOS WorkItem
   ↓
existing AEOS queue / lease / execution path
```

The adapter preserves the canonical mission/work lineage and exact baseline SHA. The generated WorkItem is deterministic from the canonical lineage, RECON failure fingerprint, and RepairSet fingerprint.

The WorkItem starts as `QUEUED`, with no lease and zero execution attempts. It carries failure and repair-set fingerprints as evidence references. Changed files and regression tests are declaratively embedded in the intent payload.

This module does **not** enqueue or execute work, grant authority, bypass forensic verification, modify Git refs, weaken gates, or merge anything.

Unknown root cause remains a hard-stop concern owned by the existing H00-H27 protocol; this bridge only accepts a completed RepairSet.
