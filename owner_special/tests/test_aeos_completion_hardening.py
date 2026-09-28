"""Negative-first regression tests for AEOS completion hardening."""
from __future__ import annotations

import unittest

from owner_special.research_os_friend.aeos_durable_work_graph import WorkGraph, WorkGraphError, WorkItem
from owner_special.research_os_friend.aeos_recovery_fabric import RecoveryError, create_checkpoint, validate_rollback_request


SHA = "a" * 40


class DurableWorkGraphTests(unittest.TestCase):
    def item(self, work_id: str, *, deps: tuple[str, ...] = (), state: str = "QUEUED", lease_id: str | None = None, evidence: tuple[str, ...] = ()) -> WorkItem:
        return WorkItem(work_id=work_id, mission_id="M1", intent="test", baseline_sha=SHA, state=state, dependencies=deps, lease_id=lease_id, evidence_refs=evidence)

    def test_dependency_cycle_is_rejected(self) -> None:
        graph = WorkGraph()
        graph.add(self.item("A", deps=("B",)))
        with self.assertRaises(WorkGraphError):
            graph.add(self.item("B", deps=("A",)))

    def test_mutation_requires_exact_lease_and_baseline(self) -> None:
        graph = WorkGraph()
        graph.add(self.item("A", lease_id="L1"))
        with self.assertRaises(WorkGraphError):
            graph.transition("A", "RUNNING", observed_sha=SHA, lease_id="L2")
        with self.assertRaises(WorkGraphError):
            graph.transition("A", "RUNNING", observed_sha="b" * 40, lease_id="L1")

    def test_ready_requires_completed_dependencies(self) -> None:
        graph = WorkGraph()
        graph.add(self.item("A"))
        graph.add(self.item("B", deps=("A",)))
        self.assertEqual(graph.ready(), ("A",))

    def test_terminal_item_is_immutable(self) -> None:
        graph = WorkGraph()
        graph.add(self.item("A", state="BLOCKED"))
        with self.assertRaises(WorkGraphError):
            graph.transition("A", "QUEUED")


class RecoveryFabricTests(unittest.TestCase):
    def test_checkpoint_is_deterministic(self) -> None:
        kwargs = dict(checkpoint_id="C1", mission_id="M1", work_id="W1", baseline_sha=SHA, state={"x": 1}, evidence_refs=("EV-1",))
        self.assertEqual(create_checkpoint(**kwargs).state_digest, create_checkpoint(**kwargs).state_digest)

    def test_rollback_requires_exact_checkpoint_evidence(self) -> None:
        checkpoint = create_checkpoint(checkpoint_id="C1", mission_id="M1", work_id="W1", baseline_sha=SHA, state={"x": 1}, evidence_refs=("EV-1",))
        with self.assertRaises(RecoveryError):
            validate_rollback_request(checkpoint, observed_sha=SHA, requested_work_id="W1", evidence_refs=("EV-2",))

    def test_rollback_rejects_stale_sha(self) -> None:
        checkpoint = create_checkpoint(checkpoint_id="C1", mission_id="M1", work_id="W1", baseline_sha=SHA, state={"x": 1}, evidence_refs=("EV-1",))
        with self.assertRaises(RecoveryError):
            validate_rollback_request(checkpoint, observed_sha="b" * 40, requested_work_id="W1", evidence_refs=("EV-1",))


if __name__ == "__main__":
    unittest.main()
