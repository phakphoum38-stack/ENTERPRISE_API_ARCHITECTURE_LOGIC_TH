# P0-5 Forensic → Evidence/Provenance

P0-5 creates the evidence binding boundary between forensic proof and the canonical identity federation.

RECON failure → forensic plan/result → failure fingerprint + forensic fingerprint → ForensicEvidence → canonical mission/work/baseline lineage → provenance hash.

The adapter is declarative. It does not execute probes, mutate source, approve authority, or certify subject truth.

`ForensicEvidence` proves that an evidence record is bound to declared canonical lineage.
`provenance_hash` proves deterministic integrity of that evidence record.
Neither alone proves that the underlying subject is true.
`independent=True` is explicit metadata from a separately governed verification path; it is never inferred.

Any mission/work/baseline mismatch fails closed.
