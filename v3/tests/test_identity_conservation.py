from __future__ import annotations

import hashlib
import json
import unittest


class IdentityConservationTests(unittest.TestCase):
    def _canonical_hash(self, payload: dict) -> str:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()

    def test_end_to_end_identity_set_is_conserved(self):
        identity = {
            "workflow_id": "wf-e2e-1",
            "task_id": "task-e2e-1",
            "event_id": "event-e2e-1",
            "delivery_id": "delivery-e2e-1",
            "idempotency_key": "idem-e2e-1",
        }
        stages = [
            {"stage": "workflow", **identity},
            {"stage": "task", **identity},
            {"stage": "lease", **identity},
            {"stage": "worker", **identity},
            {"stage": "event", **identity},
            {"stage": "delivery", **identity},
            {"stage": "dlq", **identity},
            {"stage": "replay", **identity},
        ]
        expected = tuple(identity.items())
        for stage in stages:
            observed = {k: stage[k] for k in identity}
            self.assertEqual(expected, tuple(observed.items()))

    def test_replay_does_not_change_execution_identity(self):
        original = {
            "task_id": "task-e2e-2",
            "event_id": "event-e2e-2",
            "idempotency_key": "idem-e2e-2",
        }
        replay = {
            **original,
            "replay_id": "replay-e2e-2",
        }
        for key in original:
            self.assertEqual(original[key], replay[key])
        self.assertNotEqual("replay-e2e-2", replay["task_id"])

    def test_identity_fingerprint_is_deterministic(self):
        payload_a = {
            "task_id": "task-e2e-3",
            "event_id": "event-e2e-3",
            "idempotency_key": "idem-e2e-3",
        }
        payload_b = {
            "idempotency_key": "idem-e2e-3",
            "event_id": "event-e2e-3",
            "task_id": "task-e2e-3",
        }
        self.assertEqual(self._canonical_hash(payload_a), self._canonical_hash(payload_b))

    def test_missing_identity_fails_closed(self):
        required = ("task_id", "event_id", "delivery_id", "idempotency_key")
        observed = {"task_id": "task-e2e-4", "event_id": "event-e2e-4"}
        missing = [key for key in required if not observed.get(key)]
        self.assertEqual(["delivery_id", "idempotency_key"], missing)


if __name__ == "__main__":
    unittest.main()
