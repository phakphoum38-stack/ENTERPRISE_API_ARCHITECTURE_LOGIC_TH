import tempfile
import unittest
from pathlib import Path

from tools.project_registry import ProjectRegistry
from tools.project_scale_execution import (
    SCALE_LEVELS,
    execute_scale,
    exercise_resource_conflict,
)
from tools.project_scale_readiness import build_project_definitions


SHA = "a" * 40


class ProjectScaleExecutionTests(unittest.TestCase):
    def test_real_projects_execute_at_all_scale_levels(self) -> None:
        for count in SCALE_LEVELS:
            with self.subTest(project_count=count), tempfile.TemporaryDirectory() as directory:
                registry = ProjectRegistry(build_project_definitions(count))
                summary = execute_scale(
                    registry=registry,
                    ledger_path=Path(directory) / "shared-evidence.jsonl",
                    owner_id="owner-001",
                    source_sha=SHA,
                    target_sha=SHA,
                    workflow_run_id=f"workflow-scale-{count}",
                )
                self.assertEqual(summary.project_count, count)
                self.assertEqual(summary.completed, count)
                self.assertEqual(summary.recovered, 0)
                self.assertEqual(summary.evidence_records, count * 8)

    def test_shared_evidence_plane_keeps_project_correlations_isolated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry = ProjectRegistry(build_project_definitions(2))
            summary = execute_scale(
                registry=registry,
                ledger_path=Path(directory) / "shared-evidence.jsonl",
                owner_id="owner-001",
                source_sha=SHA,
                target_sha=SHA,
                workflow_run_id="workflow-shared-evidence",
            )
            self.assertEqual(summary.completed, 2)

    def test_cross_project_capability_boundary_fails_closed_at_scale(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            definitions = list(build_project_definitions(2))
            definitions[1] = type(definitions[1])(
                project_id=definitions[1].project_id,
                display_name=definitions[1].display_name,
                version=definitions[1].version,
                capabilities=("agent",),
                authorization_policy=definitions[1].authorization_policy,
                workflow_profile=definitions[1].workflow_profile,
                evidence_namespace=definitions[1].evidence_namespace,
                resource_policy=definitions[1].resource_policy,
            )
            registry = ProjectRegistry(definitions)
            from tools.lifecycle_evidence import LifecycleEvidenceLedger
            from tools.project_execution import ProjectExecutionProof

            proof = ProjectExecutionProof(
                registry=registry,
                ledger=LifecycleEvidenceLedger(Path(directory) / "evidence.jsonl"),
                owner_id="owner-001",
                source_sha=SHA,
                target_sha=SHA,
                workflow_run_id="workflow-boundary",
            )
            with self.assertRaises(ValueError):
                proof.invoke(
                    project_id="project-002",
                    capability_id="assurance",
                    action="record evidence",
                    executor=object(),
                    correlation_id="project-002-boundary",
                    authorized=True,
                )

    def test_stale_sha_rejects_stops_releases_and_reconciles(self) -> None:
        calls = {"release": 0, "reconcile": 0}

        evidence = exercise_resource_conflict(
            Path(tempfile.mkdtemp()) / "resources.sqlite",
            release_resources=lambda: calls.__setitem__("release", calls["release"] + 1),
            reconcile_delivery=lambda _: calls.__setitem__("reconcile", calls["reconcile"] + 1),
        )

        self.assertEqual(evidence.action, "UPDATE_REJECTED")
        self.assertEqual(evidence.execution_disposition, "stop")
        self.assertEqual(evidence.resource_disposition, "release")
        self.assertEqual(evidence.delivery_disposition, "ack_or_reconcile")
        self.assertEqual(calls, {"release": 1, "reconcile": 1})

    def test_same_version_overwrite_is_rejected_and_branching_is_preserved(self) -> None:
        from v3.research_os_v3.resource_lineage import ResourceConflictError, ResourceVersionStore

        with tempfile.TemporaryDirectory() as directory:
            store = ResourceVersionStore(Path(directory) / "resources.sqlite")
            initial = store.initialize("resource-a", {"value": "A"})
            updated = store.update(
                "resource-a",
                expected_version=initial.version,
                expected_sha256=initial.content_sha256,
                content={"value": "B"},
            )
            with self.assertRaises(ResourceConflictError):
                store.update(
                    "resource-a",
                    expected_version=initial.version,
                    expected_sha256=initial.content_sha256,
                    content={"value": "C"},
                )
            branch = store.branch(
                "resource-a",
                parent_version=initial.version,
                content={"value": "C"},
            )
            self.assertEqual(branch.parent_version, initial.version)
            self.assertNotEqual(branch.version, updated.version)


if __name__ == "__main__":
    unittest.main()
