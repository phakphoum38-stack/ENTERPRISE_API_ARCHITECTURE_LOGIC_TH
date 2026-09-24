# Research OS M.2 Whole-System Audit Graph

M.2 is the descriptive repository-wide audit/index layer. This update keeps the existing inventory API and adds an explicit relationship graph.

## What it connects

- FILE -> CONTRACT references
- CONTRACT -> TEST verification relationships
- WORKFLOW -> WORKFLOW dispatch/reference signals
- FILE/WORKFLOW -> existing Unified Final Gate binding
- FILE -> architecture invariant references
- source SHA, node identity and dangling-edge integrity

The graph reuses existing repository authorities; it does not create a second Platform Graph, runtime, scheduler, authorization service, evidence authority, or release authority.

## Search

Use `python tools/research_os_m2_audit.py --query runner` or `--query final_gate`.

The query returns matching graph nodes and edges. Full output is written to `m2_audit_index.json` with the exact checked-out SHA.

## Gate semantics

`M2_AUDIT_INDEX=PASS` and `M2_AUDIT_GRAPH=PASS` mean only that the index/graph itself is source-pinned and internally consistent. They do not mean every capability is complete.

UNKNOWN, SKIPPED and DEFERRED remain non-success states. Findings remain explicit for subsequent repair/audit.

M.2 is read-only and descriptive.
