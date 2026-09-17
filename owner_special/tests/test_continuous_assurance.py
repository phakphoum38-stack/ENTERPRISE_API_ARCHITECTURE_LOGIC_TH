from __future__ import annotations

import unittest

from owner_special.research_os_friend.canonical_identity_federation import CanonicalIdentity
from owner_special.research_os_friend.continuous_supervisor import SupervisorDecision
from owner_special.research_os_friend.distributed_coordination import (
    ConcurrentProject,
    CoordinationClaim,
)
from owner_special.research_os_friend.project_fleet import FleetProject, build_fleet
from owner_special.research_os_friend.continuous_assurance import (
    ContinuousAssuranceError,
    assure_fleet,
    observe_project,
)


BASELINE = "b52f6852fd1085c72fb947fead3e4da5a26759a7"


def identity(project: str, work: str, mission: str) -> CanonicalIdentity:
    return CanonicalIdentity(
        mission_id=mission,
        work_id=work,
        baseline_sha=BASELINE,
        task_id=f"task-{project}",
        run_id=f"run-{project}",
        attempt_id=f"attempt-{project}",
    )


class ContinuousAssuranceTests(unittest.TestCase):
    def make_project(self, suffix: str = "1") -> tuple[object, ConcurrentProject]:
        ident = identity(f"project-{suffix}", f"work-{suffix}", f"mission-{suffix}")
        fleet = build_fleet(
            [FleetProject(project_id=f"project-{suffix}", identity=ident)]
        )
        concurrent = ConcurrentProject(
            project_id=f"project-{suffix}",
            identity=ident,
            max_parallel_units=4,
            active_units=2,
        )
        return fleet, concurrent

    def test_healthy_fleet_passes(self) -> None:
        fleet, project = self.make_project()
        observation = observe_project(fleet=fleet, project=project)
        summary = assure_fleet(fleet=fleet, observations=[observation])
        self.assertEqual(summary.status, "PASS")
        self.assertTrue(summary.passed)
        self.assertEqual(len(summary.assurance_fingerprint), 64)

    def test_fleet_coverage_must_match(self) -> None:
        fleet, _ = self.make_project()
        with self.assertRaisesRegex(ContinuousAssuranceError, "coverage"):
            assure_fleet(fleet=fleet, observations=[])

    def test_stale_claim_fails_closed(self) -> None:
        fleet, project = self.make_project()
        claim = CoordinationClaim(
            project_id=project.project_id,
            identity=project.identity,
            owner_id="owner-1",
            epoch=1,
            claim_id="claim-1",
        )
        with self.assertRaisesRegex(ContinuousAssuranceError, "stale"):
            observe_project(
                fleet=fleet,
                project=project,
                claim=claim,
                expected_epoch=2,
            )

    def test_inactive_claim_fails_closed(self) -> None:
        fleet, project = self.make_project()
        claim = CoordinationClaim(
            project_id=project.project_id,
            identity=project.identity,
            owner_id="owner-1",
            epoch=1,
            claim_id="claim-1",
            active=False,
        )
        with self.assertRaisesRegex(ContinuousAssuranceError, "stale"):
            observe_project(
                fleet=fleet,
                project=project,
                claim=claim,
                expected_epoch=1,
            )

    def test_quarantine_produces_hold_not_pass(self) -> None:
        fleet, project = self.make_project()
        decision = SupervisorDecision(
            action="QUARANTINE",
            identity=project.identity,
            reason="conflict detected",
        )
        observation = observe_project(
            fleet=fleet,
            project=project,
            decision=decision,
        )
        summary = assure_fleet(
            fleet=fleet,
            observations=[observation],
            decisions=[decision],
        )
        self.assertEqual(summary.status, "HOLD")
        self.assertTrue(summary.blocked)

    def test_active_retry_condition_holds(self) -> None:
        fleet, project = self.make_project()
        decision = SupervisorDecision(
            action="RETRY",
            identity=project.identity,
            reason="transient failure",
            requires_new_attempt=True,
        )
        observation = observe_project(
            fleet=fleet,
            project=project,
            decision=decision,
        )
        summary = assure_fleet(
            fleet=fleet,
            observations=[observation],
            decisions=[decision],
        )
        self.assertEqual(summary.status, "HOLD")
        self.assertIn("RETRY", summary.reasons[0])

    def test_current_claim_can_pass(self) -> None:
        fleet, project = self.make_project()
        claim = CoordinationClaim(
            project_id=project.project_id,
            identity=project.identity,
            owner_id="owner-1",
            epoch=3,
            claim_id="claim-3",
        )
        observation = observe_project(
            fleet=fleet,
            project=project,
            claim=claim,
            expected_epoch=3,
        )
        summary = assure_fleet(fleet=fleet, observations=[observation])
        self.assertEqual(summary.status, "PASS")

    def test_fleet_rejects_duplicate_work_identity(self) -> None:
        first = identity("project-1", "shared-work", "mission-1")
        second = identity("project-2", "shared-work", "mission-2")
        with self.assertRaisesRegex(Exception, "duplicate canonical work_id"):
            build_fleet([
                FleetProject("project-1", first),
                FleetProject("project-2", second),
            ])

    def test_inconsistent_fenced_claim_metadata_fails_closed(self) -> None:
        with self.assertRaisesRegex(ContinuousAssuranceError, "fenced claim must be active"):
            from owner_special.research_os_friend.continuous_assurance import FleetAssuranceObservation
            FleetAssuranceObservation(
                project_id="project-1",
                identity=identity("project-1", "work-1", "mission-1"),
                supervisor_action="NOOP",
                concurrency_active=0,
                concurrency_limit=1,
                claim_epoch=1,
                claim_active=False,
                claim_fenced=True,
            )

    def test_concurrency_is_bounded(self) -> None:
        fleet, project = self.make_project()
        observation = observe_project(fleet=fleet, project=project)
        self.assertLessEqual(
            observation.concurrency_active,
            observation.concurrency_limit,
        )

    def test_assurance_is_projection_only(self) -> None:
        fleet, project = self.make_project()
        observation = observe_project(fleet=fleet, project=project)
        summary = assure_fleet(fleet=fleet, observations=[observation])
        self.assertEqual(project.active_units, 2)
        self.assertEqual(fleet.size, 1)
        self.assertEqual(summary.status, "PASS")


if __name__ == "__main__":
    unittest.main()
