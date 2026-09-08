# Identity, Capability, Authority & Zero-Trust Agent Control

Status: CANONICAL

P0-04 implements the identity and authority plane required by Engineering Constitution P0-03. Every privileged operation must be attributable to a stable identity, constrained by an explicit capability and scope, and accompanied by reproducible authorization proof.

## Authority chain

```text
Identity
  ↓
Capability
  ↓
Grant / Delegation
  ↓
Scope + Validity + Revocation
  ↓
Authorization Proof
  ↓
Sensitive Action
```

Unknown state is denied. Revocation removes effective authority rather than merely recording an advisory status.

## Contract boundary

`current/IDENTITY_AUTHORITY_CONTRACT.json` is the machine-readable source of truth for identity types, capabilities, grants, delegation, revocation, separation of duties, sandbox boundaries, authorization proof, and fail-closed rules.

`current/IDENTITY_AUTHORITY_FIXTURE.json` is the canonical positive policy fixture used by the validator and CI.

## Core controls

- Stable identities: human, agent, service, and workflow identities have explicit status and issuer.
- Least privilege: capabilities have explicit action/resource/scope and no wildcard scope.
- No self-authorization: a subject cannot grant authority to itself; authority is attributable to an active grantor.
- Explicit delegation: delegation is time-bounded, scope-limited, and cannot escalate capability.
- Revocation: revoked identities cannot retain effective grants or authorize actions.
- Separation of duties: high-risk proposal and approval are distinct; authority changes cannot target the grantor itself.
- Sandbox boundaries: agent execution is denied by default without the required capability and resource scope.
- Proof before sensitive action: an ALLOW decision must reference an active identity and active grant with a scope no broader than the grant.

## Failure model

The validator fails closed for unknown identities, capabilities, grants, revoked subjects, expired/revoked delegation, missing scope, scope escalation, missing authorization proof, and conflicting authority.

This contract complements the constitutional rules C-002, C-003, C-004, and C-006. It does not replace human approval for high-risk constitutional actions.

## Verification

Run:

```text
python tools/validate_identity_authority.py
python -m unittest tools.test_validate_identity_authority -v
```

The CI gate executes both the canonical fixture validation and the negative regression suite.

## Handoff

Evidence and policy fixtures from this contract are the authority-plane inputs for **#322 Provenance & Evidence Ledger**. The next layer must make authorization decisions and their supporting evidence durable, traceable, and independently verifiable.
