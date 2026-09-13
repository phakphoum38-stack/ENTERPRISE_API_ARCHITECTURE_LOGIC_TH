import unittest

from owner_special.research_os_friend.evidence_provenance import (
    EvidenceRecord,
    ProvenanceChain,
    ProvenanceError,
    validate_evidence_authority,
    validate_freshness,
)


SHA_A = "a" * 40
SHA_B = "b" * 40


def record(**overrides):
    values = {
        "schema": "research-os.evidence.v1",
        "evidence_type": "ci-result",
        "source_sha": SHA_A,
        "producer": "github-actions",
        "correlation_id": "run-001",
        "observed_at": "2026-09-08T00:00:00Z",
        "payload": {"workflow": "ci", "conclusion": "failure"},
    }
    values.update(overrides)
    return EvidenceRecord(**values)


class EvidenceProvenanceTests(unittest.TestCase):
    def test_record_has_deterministic_fingerprint(self):
        self.assertEqual(record().fingerprint, record().fingerprint)
        self.assertEqual(record().source_sha, SHA_A)

    def test_payload_is_deeply_immutable(self):
        source = {"workflow": "ci", "details": {"attempt": 1}, "items": [{"state": "failed"}]}
        evidence = record(payload=source)
        source["workflow"] = "changed"
        source["details"]["attempt"] = 2
        source["items"][0]["state"] = "changed"
        self.assertEqual(evidence.payload["workflow"], "ci")
        self.assertEqual(evidence.payload["details"]["attempt"], 1)
        self.assertEqual(evidence.payload["items"][0]["state"], "failed")
        with self.assertRaises(TypeError):
            evidence.payload["new"] = "value"
        with self.assertRaises(TypeError):
            evidence.payload["details"]["attempt"] = 3
        with self.assertRaises(TypeError):
            evidence.payload["items"][0]["state"] = "changed"

    def test_fingerprint_cannot_change_after_nested_mutation_attempt(self):
        evidence = record(payload={"details": {"attempt": 1}})
        fingerprint = evidence.fingerprint
        with self.assertRaises(TypeError):
            evidence.payload["details"]["attempt"] = 2
        self.assertEqual(evidence.fingerprint, fingerprint)

    def test_chain_requires_same_source(self):
        with self.assertRaises(ProvenanceError):
            ProvenanceChain((record(), record(source_sha=SHA_B)))

    def test_chain_append_binds_parent(self):
        chain = ProvenanceChain((record(),))
        next_record = record(evidence_type="gate-result")
        extended = chain.append(next_record)
        self.assertEqual(len(extended.records), 2)
        self.assertEqual(extended.records[1].parent_fingerprint, chain.records[0].fingerprint)

    def test_append_rejects_different_source(self):
        chain = ProvenanceChain((record(),))
        with self.assertRaises(ProvenanceError):
            chain.append(record(source_sha=SHA_B))

    def test_freshness_is_exact_sha_and_correlation(self):
        evidence = record()
        self.assertTrue(validate_freshness(evidence, expected_sha=SHA_A, current_correlation_id="run-001"))
        self.assertFalse(validate_freshness(evidence, expected_sha=SHA_B, current_correlation_id="run-001"))
        self.assertFalse(validate_freshness(evidence, expected_sha=SHA_A, current_correlation_id="run-002"))

    def test_secret_like_payload_is_rejected(self):
        with self.assertRaises(ProvenanceError):
            record(payload={"api_key": "secret"})

    def test_nested_secret_like_payload_is_rejected(self):
        with self.assertRaises(ProvenanceError):
            record(payload={"details": {"token": "secret"}})

    def test_authority_fields_are_rejected(self):
        with self.assertRaises(ProvenanceError):
            validate_evidence_authority({"approved": True})

    def test_nested_authority_fields_are_rejected(self):
        with self.assertRaises(ProvenanceError):
            record(payload={"details": {"approved": True}})

    def test_authority_fields_inside_lists_are_rejected(self):
        with self.assertRaises(ProvenanceError):
            record(payload={"events": [{"authorize": True}]})

    def test_oversized_payload_is_rejected(self):
        with self.assertRaises(ProvenanceError):
            record(payload={"data": "x" * 70000})

    def test_invalid_artifact_digest_is_rejected(self):
        with self.assertRaises(ProvenanceError):
            record(artifact_sha256="not-a-digest")


if __name__ == "__main__":
    unittest.main()
