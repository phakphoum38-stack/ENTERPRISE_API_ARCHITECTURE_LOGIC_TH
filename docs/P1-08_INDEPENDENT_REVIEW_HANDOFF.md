# P1-08 Independent Review Handoff

Bind the existing `READY_FOR_REVIEW` projection to the existing AEOS Independent Technical Reviewer.

Flow:

`Certification → READY_FOR_REVIEW → Independent Review → PASS / HOLD → existing Pre-Authority path`

Rules:

- only `READY_FOR_REVIEW` material can enter this handoff;
- Independent Review must return `PASS`;
- reviewer authority must remain `REVIEW_ONLY`;
- Owner Authority remains `NOT GRANTED`;
- merge authorization remains `LOCKED`;
- the review target SHA must be an exact 40-character Git SHA and must differ from the protected baseline;
- the projection does not approve, authorize, merge, dispatch, execute, or mutate AEOS, Git, or CI.

A PASS recommends `PROCEED TO PRE-AUTHORITY`; it does not create merge authorization.
