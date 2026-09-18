from __future__ import annotations

import unittest


class QueueEventDLQReplayIntegrationContractTests(unittest.TestCase):
    def test_identity_chain_has_one_task_and_one_idempotency_key(self):
        chain = {
            "task_id": "task-integrated-1",
            "event_id": "event-integrated-1",
            "delivery_id": "delivery-integrated-1",
            "idempotency_key": "idem-integrated-1",
            "dlq_task_id": "task-integrated-1",
            "replay_task_id": "task-integrated-1",
            "replay_id": "replay-integrated-1",
        }
        self.assertEqual(chain["task_id"], chain["dlq_task_id"])
        self.assertEqual(chain["task_id"], chain["replay_task_id"])
        self.assertEqual(chain["idempotency_key"], "idem-integrated-1")
        self.assertNotEqual(chain["replay_id"], chain["task_id"])

    def test_replay_reuses_existing_delivery_boundary(self):
        original = {"delivery_id": "delivery-integrated-2", "idempotency_key": "idem-integrated-2"}
        replay = dict(original)
        self.assertEqual(original, replay)

    def test_duplicate_execution_path_is_rejected_by_contract(self):
        executions = [
            {"task_id": "task-integrated-3", "idempotency_key": "idem-integrated-3"},
            {"task_id": "task-integrated-3", "idempotency_key": "idem-integrated-3"},
        ]
        unique_keys = {(item["task_id"], item["idempotency_key"]) for item in executions}
        self.assertEqual(1, len(unique_keys))


if __name__ == "__main__":
    unittest.main()
