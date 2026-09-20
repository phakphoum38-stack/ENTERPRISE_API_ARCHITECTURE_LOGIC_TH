#!/usr/bin/env python3
import unittest

from tools.universal_control_surface import CommandSpec
from tools.workflow_resolver import WorkflowResolutionError, resolve_workflow


REGISTRY = {
    "stages": [
        {
            "stage": 70,
            "file": "ci-lite.yml",
            "dispatchable": True,
            "role": "ci-gate",
        },
        {
            "stage": 100,
            "file": "generate-orchestrator.yml",
            "dispatchable": False,
            "role": "orchestrator",
        },
    ]
}

SOURCE = """name: Generate Orchestrator
on:
  workflow_dispatch:
    inputs:
      mode:
        required: false
        default: inventory
      ref:
        required: false
"""


class WorkflowResolverTests(unittest.TestCase):
    def test_resolves_existing_non_downstream_orchestrator(self):
        command = CommandSpec(
            command_id="CMD-GENERATE-001",
            label="Run Generate Orchestrator",
            intent="Run existing Generate Orchestrator",
            target="generate-orchestrator.yml",
            mode="LIVE",
        )
        result = resolve_workflow(
            command,
            REGISTRY,
            workflow_source=SOURCE,
            target_sha="a" * 64,
        )
        self.assertEqual(result.workflow.file, "generate-orchestrator.yml")
        self.assertFalse(result.workflow.dispatchable)
        self.assertEqual(result.workflow_name, "Generate Orchestrator")
        self.assertEqual(result.dispatch_endpoint, "/actions/workflows/generate-orchestrator.yml/dispatches")
        self.assertEqual(result.input_keys, ("mode", "ref"))
        self.assertEqual(len(result.resolution_fingerprint), 64)

    def test_resolves_by_registry_role(self):
        command = CommandSpec(
            command_id="CMD-CI-001",
            label="Run CI",
            intent="Run existing CI gate",
            target="ci-gate",
        )
        result = resolve_workflow(command, REGISTRY, workflow_source=SOURCE)
        self.assertEqual(result.workflow.file, "ci-lite.yml")

    def test_rejects_unknown_target(self):
        command = CommandSpec(
            command_id="CMD-UNKNOWN",
            label="Run unknown",
            intent="Unknown workflow",
            target="does-not-exist.yml",
        )
        with self.assertRaises(WorkflowResolutionError):
            resolve_workflow(command, REGISTRY, workflow_source=SOURCE)

    def test_rejects_missing_dispatch_contract(self):
        command = CommandSpec(
            command_id="CMD-CI-001",
            label="Run CI",
            intent="Run existing CI gate",
            target="ci-lite.yml",
        )
        with self.assertRaises(WorkflowResolutionError):
            resolve_workflow(command, REGISTRY, workflow_source="name: CI\n")

    def test_rejects_non_sha_target(self):
        command = CommandSpec(
            command_id="CMD-GENERATE-001",
            label="Run Generate Orchestrator",
            intent="Run existing Generate Orchestrator",
            target="generate-orchestrator.yml",
        )
        with self.assertRaises(WorkflowResolutionError):
            resolve_workflow(command, REGISTRY, workflow_source=SOURCE, target_sha="main")


if __name__ == "__main__":
    unittest.main()
