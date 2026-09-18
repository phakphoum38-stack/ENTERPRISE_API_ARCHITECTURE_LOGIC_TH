# Scenario Algebra Usage

Reusable logical scenario composer for V3 runtime assurance. It computes exact Cartesian-product cardinality, validates scenarios fail-closed, creates deterministic SHA-256 scenario IDs, and supports bounded sampling. It never executes scenarios, enqueues tasks, creates workers, dispatches workflows, or mutates runtime state. Use cardinality plus deterministic IDs and bounded representative sampling for very large coverage targets such as 10^1000.
