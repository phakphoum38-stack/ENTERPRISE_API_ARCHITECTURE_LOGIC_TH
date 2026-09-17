import unittest
from types import SimpleNamespace
from owner_special.research_os_friend.canonical_identity_federation import CanonicalIdentity
from owner_special.research_os_friend.p1_resource_execution_binding import P1ResourceBindingError, bind_resource_execution

SHA = "a" * 40

class P1ResourceExecutionBindingTests(unittest.TestCase):
    def identity(self):
        return CanonicalIdentity("mission-1", "work-1", SHA, task_id="task-1", run_id="run-1", attempt_id="attempt-1")
    def result(self):
        return SimpleNamespace(
            request_id="request-1",
            admission=SimpleNamespace(reservation_id="admission-1", principal_id="owner-1", decision=SimpleNamespace(value="allow")),
            provider="provider-x",
            model="model-y",
            ledger_entry=SimpleNamespace(entry_hash="b" * 64),
            evidence={"evidence_hash": "c" * 64},
        )
    def test_binds_existing_resource_result(self):
        bound = bind_resource_execution(identity=self.identity(), execution_result=self.result())
        self.assertEqual(bound.resource.request_id, "request-1")
        self.assertEqual(bound.resource.admission_id, "admission-1")
        self.assertEqual(bound.resource.principal_id, "owner-1")
        self.assertEqual(len(bound.binding_hash), 64)
    def test_denied_or_unreserved_result_fails_closed(self):
        result = self.result()
        result.admission.reservation_id = None
        with self.assertRaises(P1ResourceBindingError):
            bind_resource_execution(identity=self.identity(), execution_result=result)
    def test_bad_ledger_hash_fails_closed(self):
        result = self.result()
        result.ledger_entry = SimpleNamespace(entry_hash="not-sha256")
        with self.assertRaises(P1ResourceBindingError):
            bind_resource_execution(identity=self.identity(), execution_result=result)

if __name__ == "__main__":
    unittest.main()
