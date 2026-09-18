# P1-14 Project Namespace Isolation

P1-14 establishes namespace isolation for the 10^10 logical-project federation.

A project address is scoped by:

- mission namespace
- project_id
- deterministic partition/slot

The canonical identity remains authoritative. Namespace routing cannot alter
mission, work, or baseline lineage.

The same project_id may exist in different mission namespaces without becoming
the same logical project key.

This remains a pure projection/validation boundary. It does not create or
modify schedulers, queues, workers, execution engines, authority, merge paths,
or CI.
