from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.project_registry import (
    FINAL_GATE,
    PROJECT_001,
    SHARED_CAPABILITY_REGISTRY,
    SHARED_EVIDENCE_LEDGER,
    SHARED_QUEUE,
    ProjectDefinition,
    ProjectRegistry,
    validate_registry,
)


class ProjectRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = ProjectRegistry((PROJECT_001,))

    def test_project_template_contract_and_reference_match_registry(self) -> None:
        root = Path(__file__).resolve().parents[1]
        contract = json.loads(
            (root / "current/RESEARCH_OS_PROJECT_TEMPLATE_CONTRACT.json").read_text(
                encoding="utf-8"
            )
        )
        reference = json.loads(
            (root / "current/RESEARCH_OS_PROJECT_001.json").read_text(encoding="utf-8")
        )
        self.assertEqual(contract["status"], "ACTIVE")
        self.assertEqual(
            contract["reference_project"],
            "current/RESEARCH_OS_PROJECT_001.json",
        )
        self.assertEqual(reference["project_id"], PROJECT_001.project_id)
        self.assertEqual(reference["version"], PROJECT_001.version)
        self.assertEqual(tuple(reference["capabilities"]), PROJECT_001.capabilities)

    def test_project_001_is_reference_configuration(self) -> None:
        project = self.registry.get("project-001")
        self.assertEqual(project.project_id, "project-001")
        self.assertEqual(project.release_authority, FINAL_GATE)
        self.assertEqual(project.capability_namespace, SHARED_CAPABILITY_REGISTRY)
        self.assertEqual(project.queue_namespace, SHARED_QUEUE)
        self.assertEqual(project.evidence_ledger, SHARED_EVIDENCE_LEDGER)
        self.assertEqual(project.evidence_namespace, "PROJECT:project-001")

    def test_capabilities_resolve_through_canonical_registry(self) -> None:
        self.assertEqual(validate_registry((PROJECT_001,)), ())

    def test_duplicate_project_id_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            ProjectRegistry((PROJECT_001, PROJECT_001))

    def test_unknown_capability_fails_closed(self) -> None:
        project = ProjectDefinition(
            project_id="project-unknown",
            display_name="Unknown Capability",
            version="1.0.0",
            capabilities=("not_a_canonical_capability",),
            authorization_policy="EXISTING_AUTHORIZATION_BOUNDARY",
            workflow_profile="SHARED_WORKFLOW",
            evidence_namespace="PROJECT:project-unknown",
            resource_policy="REJECT_ON_CONFLICT",
        )
        with self.assertRaises(KeyError):
            ProjectRegistry((project,))

    def test_project_specific_runtime_queue_evidence_are_forbidden(self) -> None:
        with self.assertRaises(ValueError):
            ProjectDefinition(
                project_id="project-002",
                display_name="Invalid",
                version="1.0.0",
                capabilities=("agent",),
                authorization_policy="EXISTING_AUTHORIZATION_BOUNDARY",
                workflow_profile="SHARED_WORKFLOW",
                evidence_namespace="PROJECT:project-002",
                resource_policy="REJECT_ON_CONFLICT",
                queue_namespace="QUEUE:project-002",
            )

    def test_second_release_authority_is_forbidden(self) -> None:
        with self.assertRaises(ValueError):
            ProjectDefinition(
                project_id="project-002",
                display_name="Invalid",
                version="1.0.0",
                capabilities=("agent",),
                authorization_policy="EXISTING_AUTHORIZATION_BOUNDARY",
                workflow_profile="SHARED_WORKFLOW",
                evidence_namespace="PROJECT:project-002",
                resource_policy="REJECT_ON_CONFLICT",
                release_authority="PROJECT_GATE",
            )

    def test_idempotency_is_project_scoped(self) -> None:
        project_002 = ProjectDefinition(
            project_id="project-002",
            display_name="Second Project",
            version="1.0.0",
            capabilities=("agent",),
            authorization_policy="EXISTING_AUTHORIZATION_BOUNDARY",
            workflow_profile="SHARED_WORKFLOW",
            evidence_namespace="PROJECT:project-002",
            resource_policy="REJECT_ON_CONFLICT",
        )
        registry = ProjectRegistry((PROJECT_001, project_002))
        first = registry.build_idempotency_key(
            project_id="project-001",
            event_id="event-1",
            source_sha="a" * 40,
            action="execute",
        )
        second = registry.build_idempotency_key(
            project_id="project-002",
            event_id="event-1",
            source_sha="a" * 40,
            action="execute",
        )
        self.assertNotEqual(first, second)
        self.assertTrue(first.startswith("project-001|"))
        self.assertTrue(second.startswith("project-002|"))

    def test_real_project_definitions_scale_at_10_20_50_100(self) -> None:
        for count in (10, 20, 50, 100):
            registry = ProjectRegistry()
            for index in range(1, count + 1):
                registry.register(
                    ProjectDefinition(
                        project_id=f"project-{index:03d}",
                        display_name=f"Project {index:03d}",
                        version="1.0.0",
                        capabilities=("agent",),
                        authorization_policy="EXISTING_AUTHORIZATION_BOUNDARY",
                        workflow_profile="SHARED_WORKFLOW",
                        evidence_namespace=f"PROJECT:project-{index:03d}",
                        resource_policy="REJECT_ON_CONFLICT",
                    )
                )
            self.assertEqual(count, len(registry.all()))
            self.assertEqual(
                len(registry.all()),
                len({item.project_id for item in registry.all()}),
            )


if __name__ == "__main__":
    unittest.main()
