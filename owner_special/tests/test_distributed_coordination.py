"""Regression tests for P0-9 distributed/concurrent coordination."""
import unittest

from owner_special.research_os_friend.canonical_identity_federation import CanonicalIdentity
from owner_special.research_os_friend.distributed_coordination import (
    ConcurrentProject,
    CoordinationClaim,
    DistributedCoordinationError,
    deactivate,
    next_epoch,
    validate_claim,
)
from owner_special.research_os_friend.project_fleet import ProjectFleet, FleetProject


class DistributedCoordinationTests(unittest.TestCase):
    def setUp(self):
        self.identity = CanonicalIdentity(
            "M1", "W1", "a" * 40, task_id="T1", run_id="R1", attempt_id="A1"
        )
        self.fleet = ProjectFleet().register(FleetProject("P1", self.identity))

    def claim(self):
        return CoordinationClaim("P1", self.identity, "owner-1", 1, "claim-1")

    def test_bounded_concurrency(self):
        project = ConcurrentProject("P1", self.identity, max_parallel_units=2)
        project = project.acquire_slot().acquire_slot()
        self.assertEqual(project.active_units, 2)
        with self.assertRaises(DistributedCoordinationError):
            project.acquire_slot()

    def test_release_slot_is_immutable(self):
        project = ConcurrentProject("P1", self.identity, max_parallel_units=2).acquire_slot()
        released = project.release_slot()
        self.assertEqual(project.active_units, 1)
        self.assertEqual(released.active_units, 0)

    def test_current_claim_is_accepted(self):
        validate_claim(fleet=self.fleet, claim=self.claim(), expected_epoch=1)

    def test_stale_claim_fails_closed(self):
        with self.assertRaises(DistributedCoordinationError):
            validate_claim(fleet=self.fleet, claim=self.claim(), expected_epoch=2)

    def test_inactive_claim_fails_closed(self):
        with self.assertRaises(DistributedCoordinationError):
            validate_claim(fleet=self.fleet, claim=deactivate(self.claim()), expected_epoch=1)

    def test_epoch_fencing(self):
        newer = next_epoch(self.claim())
        self.assertEqual(newer.epoch, 2)
        with self.assertRaises(DistributedCoordinationError):
            validate_claim(fleet=self.fleet, claim=self.claim(), expected_epoch=2)
        validate_claim(fleet=self.fleet, claim=newer, expected_epoch=2)

    def test_foreign_identity_fails_closed(self):
        foreign = CoordinationClaim(
            "P1",
            CanonicalIdentity("M2", "W2", "a" * 40, task_id="T2", run_id="R2", attempt_id="A2"),
            "owner-2",
            1,
            "claim-2",
        )
        with self.assertRaises(DistributedCoordinationError):
            validate_claim(fleet=self.fleet, claim=foreign, expected_epoch=1)


if __name__ == "__main__":
    unittest.main()
