# GitHub 100PROJECT Continuous Assurance

This contract extends the existing AEOS 100 engineering-domain model into a GitHub-wide assurance control plane.

## Operating loop

`DISCOVER → INVENTORY → VERIFY → EVIDENCE → DRIFT DETECT → RECONCILE → VERIFY AGAIN → CONTINUE`

The control plane is continuous and recoverable, not an always-on worker. It uses event-driven runs, scheduled reconciliation, checkpoints, replay-safe processing, gap detection, bounded retries, watchdogs, and post-change verification.

## 100 surfaces

The machine contract enumerates P01–P100. A surface is evaluated as **PASS, FAIL, HOLD, UNKNOWN, UNAVAILABLE, NOT_APPLICABLE, or INSUFFICIENT_SCOPE**. Unknown or insufficient authority never becomes PASS implicitly.

## #457 regression boundary

Malformed Git tree/path entries are explicitly covered by P34–P37. The verifier must compare the declared changed-file set with GitHub's observed tree/path data and fail closed on impossible or malformed paths. This prevents a checkout cascade from being misclassified as 25 independent source failures.

## Authority boundary

The assurance plane may inspect, correlate, preserve evidence, and create bounded investigation/repair proposals. It does not grant permissions, alter branch protection/rulesets, approve reviews, merge PRs, enable auto-merge, rewrite canonical history, or disable required checks. Existing Recon/Owner merge authority remains outside the monitor.

## Capability discovery

Each surface must distinguish:
- PASS / FAIL: the capability was observable and verified.
- UNKNOWN: observation was attempted but truth could not be established.
- UNAVAILABLE: the API/provider capability is not exposed.
- NOT_APPLICABLE: the surface does not apply.
- INSUFFICIENT_SCOPE: the token cannot inspect it.

This prevents "GitHub-wide" from being confused with "everything the current token can see."

## Continuity

Every run should bind to a run id, source event/ref, checkpoint, contract version, and evidence fingerprint. Resume is idempotent. Missing events are found by scheduled reconciliation. A watchdog detects stale checkpoints. A full periodic audit proves scan completeness.

## Drain rule

The system stops only on a proven drain state: no required work, unresolved failure, unknown, stale state, unverified change, or blocked required dependency. Otherwise it continues or enters HOLD with evidence.

## Relationship to 100PROJECT

The existing AEOS registry already defines 100 assurance sets. This contract is a GitHub control-plane realization of the same 100-domain depth; it does not replace the existing registry or grant new authority.
