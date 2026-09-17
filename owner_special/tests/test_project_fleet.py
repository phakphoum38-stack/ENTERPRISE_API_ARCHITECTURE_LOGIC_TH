"""Regression tests for P0-8 bounded 100-project fleet federation."""
import unittest

from owner_special.research_os_friend.canonical_identity_federation import CanonicalIdentity
from owner_special.research_os_friend.continuous_supervisor import SupervisorDecision
from owner_special.research_os_friend.project_fleet import (
    MAX_PROJECTS,
    FleetProject,
    ProjectFleet,
    ProjectFleetError,
)


class ProjectFleetTests(unittest.TestCase):
    def project(self, n: int) -> FleetProject:
        return FleetProject(
            project_id=f"P{n}",
            identity=CanonicalIdentity(
                mission_id=f"M{n}",
                work_id=f"W{n}",
                baseline_sha="a" * 40,
                task_id=f"T{n}",
                run_id=f"R{n}",
                attempt_id=f"A{n}",
            ),
        )

    def test_capacity_is_100(self):
        self.assertEqual(ProjectFleet().capacity, 100)
        self.assertEqual(MAX_PROJECTS, 100)

    def test_registers_projects_without_execution(self):
        fleet = ProjectFleet().register(self.project(1)).register(self.project(2))
        self.assertEqual(fleet.size, 2)
        self.assertEqual(fleet.remaining, 98)
        self.assertEqual(fleet.get("P1").supervisor_action, "NOOP")

    def test_capacity_fails_closed(self):
        fleet = ProjectFleet(tuple(self.project(i) for i in range(100)))
        with self.assertRaises(ProjectFleetError):
            fleet.register(self.project(101))

    def test_duplicate_project_work_and_mission_are_rejected(self):
        fleet = ProjectFleet().register(self.project(1))
        with self.assertRaises(ProjectFleetError):
            fleet.register(self.project(1))
        duplicate_work = FleetProject(
            "P2",
            CanonicalIdentity("M2", "W1", "a" * 40, task_id="T2", run_id="R2", attempt_id="A2"),
        )
        with self.assertRaises(ProjectFleetError):
            fleet.register(duplicate_work)
        duplicate_mission = FleetProject(
            "P3",
            CanonicalIdentity("M1", "W3", "a" * 40, task_id="T3", run_id="R3", attempt_id="A3"),
        )
        with self.assertRaises(ProjectFleetError):
            fleet.register(duplicate_mission)

    def test_supervisor_decision_is_recorded_not_applied(self):
        fleet = ProjectFleet().register(self.project(1))
        identity = fleet.get("P1").identity
        decision = SupervisorDecision(
            "SCHEDULE", identity, "dependencies satisfied"
        )
        updated = fleet.with_decision(decision)
        self.assertEqual(updated.get("P1").supervisor_action, "SCHEDULE")
        self.assertEqual(fleet.get("P1").supervisor_action, "NOOP")

    def test_mismatched_supervisor_decision_fails_closed(self):
        fleet = ProjectFleet().register(self.project(1))
        foreign = self.project(2).identity
        decision = SupervisorDecision("SCHEDULE", foreign, "foreign identity")
        with self.assertRaises(ProjectFleetError):
            fleet.with_decision(decision)

    def test_remove_returns_new_fleet(self):
        fleet = ProjectFleet().register(self.project(1)).register(self.project(2))
        updated = fleet.remove("P1")
        self.assertEqual(fleet.size, 2)
        self.assertEqual(updated.size, 1)
        self.assertEqual(updated.get("P2").project_id, "P2")


if __name__ == "__main__":
    unittest.main()
