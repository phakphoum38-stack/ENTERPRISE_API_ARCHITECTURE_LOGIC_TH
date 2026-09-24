# Research OS M.2 Whole-System Audit Index

The M.2 index is a descriptive audit/index layer. It is not a runtime, scheduler, authorization system, evidence authority, or release authority.

## Source identity

The index is generated from the exact checked-out Git SHA. GitHub Main remains the source of truth; the virtual workspace is only an audit snapshot.

## Indexed dimensions

- file and directory inventory
- capability classification
- authority signals
- contract / implementation / test relationships
- workflow inventory
- evidence / provenance signals
- architecture invariants
- platform surfaces
- source and artifact lineage signals
- explicit GAP states: MISSING, INCOMPLETE, BROKEN, DRIFT, DUPLICATE, UNKNOWN, DEFERRED

## Search

Use `python tools/research_os_m2_audit.py --query runner` or `--query final_gate` for focused search.

Use `python tools/research_os_m2_audit.py --output m2_audit_index.json` for the complete machine-readable index.

## Gate semantics

`M2_AUDIT_INDEX=PASS` means the index itself is internally valid and source identity is pinned. It does not mean every indexed capability is complete. Findings remain explicit for subsequent repair and audit.
