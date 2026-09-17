"""Regression tests for P0-3 execution-plane mappings."""
from __future__ import annotations
import unittest
from types import SimpleNamespace
from owner_special.research_os_friend.canonical_attempt_identity import first_attempt
from owner_special.research_os_friend.canonical_execution_mapping import (
    ExecutionMappingError, bind_aeos_work, bind_api_step, bind_friend_run, bind_v3_task,
)
from owner_special.research_os_friend.canonical_identity_federation import CanonicalIdentity

SHA="a"*40

class ExecutionMappingTests(unittest.TestCase):
    def _identity(self):
        return CanonicalIdentity("M1","W1",SHA)
    def _attempt(self):
        return first_attempt(mission_id="M1",work_id="W1",task_id="CT1",run_id="R1",attempt_id="A1")
    def test_api_retry_can_change_native_task_id(self):
        a=self._attempt(); identity=self._identity().bind(task_id="CT1",run_id="R1")
        b=bind_api_step(identity=identity,step={"step_id":"S1","task_id":"native-api-task-2"},attempt=a)
        self.assertEqual(b.native_task_id,"native-api-task-2")
        self.assertEqual(b.canonical.attempt_id,"A1")
    def test_v3_native_task_id_can_remain_stable(self):
        a=self._attempt(); identity=self._identity().bind(task_id="CT1",run_id="R1")
        b=bind_v3_task(identity=identity,research_task=SimpleNamespace(id="RT1"),queue_task=SimpleNamespace(task_id="Q1"),attempt=a)
        self.assertEqual(b.native_task_id,"Q1")
        self.assertEqual(b.native_step_id,"RT1")
    def test_friend_run_must_match_canonical_run(self):
        a=self._attempt(); identity=self._identity().bind(task_id="CT1",run_id="R1")
        with self.assertRaisesRegex(ExecutionMappingError,"does not match canonical run_id"):
            bind_friend_run(identity=identity,agent_run=SimpleNamespace(run_id="R2"),attempt=a)
    def test_aeos_work_requires_exact_lineage(self):
        a=self._attempt(); identity=self._identity()
        b=bind_aeos_work(identity=identity,work_item=SimpleNamespace(work_id="W1",mission_id="M1",baseline_sha=SHA),task_id="CT1",run_id="R1",attempt=a)
        self.assertEqual(b.plane,"aeos")
    def test_api_native_task_is_not_canonical_task(self):
        a=self._attempt(); identity=self._identity().bind(task_id="CT1",run_id="R1")
        b=bind_api_step(identity=identity,step={"step_id":"S1","task_id":"native-uuid"},attempt=a)
        self.assertNotEqual(b.native_task_id,b.canonical.task_id)
if __name__=="__main__": unittest.main()
