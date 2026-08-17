# Brain + Generate Integration Contract

Use the existing Brain Runtime/Brain Core as Generate's reasoning layer. Do not create a duplicate Brain.

Flow: failure evidence -> verified Skill Memory -> Brain plan -> Tool Registry -> repair branch -> generated/edit -> validate -> Evidence -> Skill Memory promotion -> PR -> merge -> resume.

Safety: never mutate `main` directly; every tool call must be registered and attributable; unverified repairs never enter Skill Memory; learned skills retain source run, commit, PR, tools, and validation evidence.

Flutter/Dart is a registered capability and must use the same branch-first validation and PR path.