# Engineering Constitution

Status: CANONICAL

The Engineering Constitution is the governance layer above the Engineering World Model. It defines non-negotiable invariants, authority boundaries, high-risk actions, amendment lifecycle, emergency handling, and historical reconstruction.

## Relationship to P0-02

P0-02 remains the canonical vocabulary for lifecycle entities and relationships. Governance records must use its concepts rather than creating a parallel lineage model. The constitution explicitly depends on decision, contract, evidence, gate, and knowledge entities and on `decides`, `constrains`, `supported_by`, `enforced_by`, and `learns_from` relationships.

## Constitutional Rules

1. No change bypasses a declared invariant.
2. No agent, workflow, tool, or runtime may self-escalate authority.
3. High-risk mutable actions require human authority unless the bounded emergency protocol applies.
4. Governance and amendments require reproducible evidence.
5. Constitutional history is append-only; supersession must be explicit.
6. Unknown, missing, contradictory, or unverifiable authority state fails closed.

Existing architecture invariants remain binding; the constitution governs how those invariants may be changed, delegated, or enforced. The repository's invariant enforcement model is `invariant → contract/schema → test → validator/audit → CI gate → release/installed gate`.

## Authority

`human_owner` holds constitutional approval, high-risk approval, and emergency override powers. Agents may propose and analyze and may execute only within granted capability. Workflows validate, gate, record evidence, and execute only pre-approved actions. Runtime services execute granted operations and emit evidence/incidents.

No automated actor can grant itself authority or approve its own high-risk authority escalation.

## High-Risk Actions

Authority changes, constitutional amendments, production mutations, release promotion, installed artifact changes, security-policy changes, and identity/capability revocation are high-risk classes.

## Amendment Protocol

An amendment is `proposed → reviewed → approved → effective → superseded → retired`.

Every amendment records its base and target versions, proposer, reason, changes, evidence IDs, approval authority/status, and effective time. Target version must increase. Approval and evidence are mandatory. Supersession is explicit. Previous effective versions are never silently rewritten.

## Emergency Protocol

Emergency handling is permitted only through `human_owner`, is reasoned and evidence-backed, time-bounded, and requires post-event review. Emergency handling does not authorize silent constitutional history rewriting.

## Machine Enforcement

`current/ENGINEERING_CONSTITUTION.json` is the canonical machine-readable contract. `tools/validate_engineering_constitution.py` is fail-closed and emits structured PASS/FAIL output. Regression tests cover valid state, self-granted authority, missing human authority, and invalid amendment approval. CI executes both validator and tests.

## Handoff to #321

P0-03 hands #321 a canonical authority vocabulary and explicit constitutional boundaries. Identity/capability implementation must not weaken the non-escalation, human high-risk approval, evidence, append-only history, or fail-closed rules.
