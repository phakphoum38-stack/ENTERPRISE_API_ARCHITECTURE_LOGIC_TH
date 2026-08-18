import unittest

from v3.dlq.audit import ReplayAuditLog, ReplayAuthorizer


class ReplayAuditTests(unittest.TestCase):
    def test_authorized_actor_is_allowed(self):
        authorizer = ReplayAuthorizer({"operator-1"})
        self.assertTrue(authorizer.authorize("operator-1"))
        self.assertFalse(authorizer.authorize("operator-2"))

    def test_replay_decision_is_audited(self):
        audit = ReplayAuditLog()
        audit.record("task-1", "operator-1", "replay", True)
        audit.record("task-2", "operator-2", "replay", False, "not authorized")

        events = audit.events()
        self.assertEqual(2, len(events))
        self.assertTrue(events[0].authorized)
        self.assertFalse(events[1].authorized)
        self.assertEqual("not authorized", events[1].reason)
        self.assertEqual("replay", events[0].action)


if __name__ == "__main__":
    unittest.main()
