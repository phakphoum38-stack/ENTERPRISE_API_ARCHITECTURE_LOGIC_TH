# Generate Skill Memory

Verified skills are derived from successful Evidence records.

## Required fields

- skill_id
- trigger/failure pattern
- brain/decision source
- tools used
- source workflow run
- source commit
- changed files
- validation result
- PR reference
- verification timestamp
- confidence

## Promotion rule

`candidate -> validated -> reusable`

Only `validated` skills may be reused automatically. A failed or unverified repair remains evidence only.

## Retention rule

Keep the evidence references with the skill so the Brain can re-check the original reasoning and validation instead of relying on an ungrounded memory.
