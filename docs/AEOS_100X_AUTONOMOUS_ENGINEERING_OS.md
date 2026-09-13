# AEOS 100X — Autonomous Engineering Operating System

**Status:** ARCHITECTURE DRAFT — implementation and certification required  
**Baseline:** `c04d60b36d51eb8529a4c65a61c7d5a411e5fe85`  
**Mode:** `AUTO_GUARDED`  
**Auto-merge:** `OFF` until separately certified

## Mission

AEOS turns a user-level engineering mission into a durable, dependency-aware work graph and executes the complete governed lifecycle without requiring task-by-task human prompting.

The system continues automatically while governed work remains. It stops only after a final drain verification proves there is no required work, unresolved failure, unknown, stale state, unverified change, or blocked dependency.

## Non-negotiable lifecycle

```text
MISSION
 -> CONTRACT
 -> PLAN
 -> WORK GRAPH
 -> BRANCH
 -> DOCUMENT
 -> IMPLEMENT
 -> DIFF
 -> TEST
 -> CI
 -> FORENSICS
 -> ROOT-CAUSE FIX
 -> REGRESSION
 -> EVIDENCE
 -> PROVENANCE
 -> AUTHORITY AUDIT
 -> FINAL GATE
 -> CERTIFY
 -> MERGE
 -> VERIFY MAIN
 -> RE-ANCHOR
 -> NEXT WORK
 -> ...
 -> DRAIN VERIFICATION
 -> CERTIFIED IDLE
 -> STOP
```

A failure never authorizes a shortcut. `MERGE` is integration, not repair.

## Truth hierarchy

Observable state outranks agent narrative:

```text
Canonical Git SHA
  > GitHub PR / ref state
  > authoritative CI
  > artifact / evidence records
  > agent memory
  > agent narrative
```

Claims that conflict with independently observable state are rejected and recorded as evidence.

## 100 engineering domains

1. Foundation  2. Identity  3. Trust  4. Authority  5. Capability  6. Policy  7. Contract  8. Version  9. Compatibility  10. Configuration
11. Mission  12. Intent  13. Planning  14. Work Graph  15. Dependency  16. Priority  17. Scheduling  18. Queue  19. Leasing  20. Concurrency
21. Agent  22. Agent Identity  23. Agent Reputation  24. Agent Memory  25. Agent Capability  26. Agent Sandbox  27. Agent Lifecycle  28. Agent Federation  29. Agent Communication  30. Agent Governance
31. Source Control  32. Branching  33. Commit  34. Diff  35. Semantic Diff  36. Code Review  37. Pull Request  38. Merge  39. Main Protection  40. History Integrity
41. Build  42. Test  43. Regression  44. CI  45. CD  46. Artifact  47. Environment  48. Reproducibility  49. Supply Chain  50. Release
51. Evidence  52. Provenance  53. Attestation  54. Fingerprint  55. Evidence Freshness  56. Evidence Independence  57. Evidence Replay  58. Evidence Retention  59. Evidence GC  60. Evidence Integrity
61. Forensics  62. Root Cause  63. Causal Graph  64. Failure Memory  65. Incident  66. Recovery  67. Rollback  68. Disaster Recovery  69. Chaos Engineering  70. Resilience
71. Security  72. Secrets  73. Privacy  74. PII  75. Sandbox Security  76. Tool Security  77. Prompt Injection Defense  78. Supply Chain Security  79. Threat Modeling  80. Adversarial Verification
81. Observability  82. Telemetry  83. Audit  84. Event Sourcing  85. Time Travel  86. State Reconciliation  87. Truth Hierarchy  88. Anomaly Detection  89. Drift Detection  90. Health
91. Governance  92. Human Oversight  93. Certification  94. Risk  95. Cost  96. Autonomy  97. Compliance  98. Knowledge  99. Architecture Evolution  100. Mission Completion

## Control model

Every control is machine-checkable and carries:

```text
control_id
version
input_contract
preconditions
action
postconditions
evidence_requirements
verifier
authority
risk
failure_state
recovery_path
termination_rule
```

## Autonomous Supervisor

The Supervisor coordinates Planner, Builder, Tester, Forensic Investigator, Evidence/Provenance workers, Independent Verifier, Recovery worker, and Certification worker. No worker may grant itself authority or weaken its own evaluation contract.

## Safety boundaries

- `UNKNOWN` is a first-class state and never becomes `PASS` implicitly.
- Stale or conflicting baseline invalidates dependent work and forces re-anchor.
- Evidence is descriptive proof, never authority.
- No self-certification.
- No silent mutation.
- No fabricated evidence.
- No governance self-modification.
- No irreversible action without a recovery path.
- High-risk authority remains outside ordinary autonomous execution.
- #344 remains immutable/read-only.
- P0-06 #345 remains forensic hold until independently resolved and certified.

## Failure protocol

```text
FAIL
 -> preserve evidence
 -> classify
 -> reproduce
 -> generate hypotheses
 -> verify root cause
 -> apply minimal source fix
 -> regenerate diff
 -> regression
 -> authoritative CI
 -> evidence/provenance
 -> final gate
```

Retries without new evidence are not considered root-cause progress.

## Completion protocol

`PR merged` is not sufficient for mission completion. Completion requires:

```text
MAIN_VERIFIED
+ WORK_GRAPH_EMPTY
+ REQUIRED_QUEUE_EMPTY
+ RECOVERY_QUEUE_EMPTY
+ NO_UNRESOLVED_FAILURE
+ NO_UNKNOWN
+ NO_STALE
+ NO_UNVERIFIED_CHANGE
+ NO_BLOCKED_REQUIRED_DEPENDENCY
+ STOP_PROOF_PASS
```

## Autonomy ladder

```text
A0 OBSERVE
A1 RECOMMEND
A2 PREPARE
A3 SANDBOX EXECUTE
A4 GUARDED EXECUTE
A5 GOVERNED INTEGRATE
A6 CONTINUOUS AUTONOMOUS
```

AEOS starts at `AUTO_GUARDED`. Promotion requires independent verification and policy certification; autonomy is earned, not self-declared.
