# P1-09 Pre-Authority Projection

Project the existing Independent Review PASS into the existing AEOS Pre-Authority gate.

Flow:

`P1-08 Independent Review PASS → existing AuthorityPacket → READY_FOR_AUTHORITY / HOLD / BLOCKED`

Rules:

- reviewed target SHA must exactly equal the pre-authority source SHA;
- protected baseline must remain distinct from the reviewed target;
- existing AEOS `AuthorityPacket` remains the gate authority;
- all existing wave, provenance, evidence, scope, root-cause, independent-review, and assurance checks remain fail-closed;
- `READY_FOR_AUTHORITY` means the existing gate is ready for the owner-authority boundary; it does not itself grant Owner Authority or merge permission;
- no new authority engine, scheduler, queue, worker, state machine, or merge path is introduced.
