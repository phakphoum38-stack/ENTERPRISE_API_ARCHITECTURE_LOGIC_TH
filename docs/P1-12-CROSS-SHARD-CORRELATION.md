# P1-12 Cross-Shard Correlation

Adds a pure correlation projection between:

- 10^10 logical project addressing
- Canonical Identity
- the completed P1 functional integration trace

It verifies that the address is deterministically derived from the same mission
namespace and that the integration trace has the same canonical lineage.

It does not execute work, schedule work, create queues/workers, grant authority,
authorize merge, or mutate CI.

The correlation fingerprint is SHA-256 over the deterministic address,
canonical identity fingerprint, and P1 integration fingerprint.
