# Generate AI Repair Contract

## Purpose

Define the branch-only repair boundary for Generate Orchestrator.

## Flow

Observe failure -> collect evidence -> consult Brain/Skill Memory -> select registered tools -> generate/edit on repair branch -> validate -> emit evidence -> open PR -> resume only after merge.

## Safety

- Never mutate `main` directly.
- A repair run must identify its source commit and source workflow run.
- Generated edits must be attributable to a tool and evidence record.
- Failed validation must not be promoted to Skill Memory.
- A skill becomes reusable only after successful validation.

## AI inputs

- GitHub workflow/run/job evidence
- repository source and generated artifacts
- GitHub documentation references
- Tool Registry
- verified Skill Memory

## AI outputs

- repair plan
- selected tools
- changed files
- validation results
- evidence record
- proposed PR

## Memory rule

Evidence is the durable record. Skill Memory is derived from successful evidence and must retain the source run, commit, PR, tools, and validation result.
