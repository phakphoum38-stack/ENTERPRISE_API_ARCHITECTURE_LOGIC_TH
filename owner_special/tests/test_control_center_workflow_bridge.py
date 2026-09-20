#!/usr/bin/env python3
import unittest

from tools.native_control_center import ControlCommand, NativeControlCenter
from tools.workflow_execution_adapter import (
    GitHubWorkflowExecutionAdapter,
    WorkflowExecutionObservation,
)
from tools.workflow_resolver import ResolvedWorkflow, WorkflowTarget
from tools.control_center_workflow_bridge import ControlCenterWorkflowBridge


RESOLUTION = ResolvedWorkflow(
    command_id="CMD-GENERATE-001",
    command_fingerprint="a" * 64,
    workflow=WorkflowTarget("generate-orchestrator.yml", 100, "orchestrator", False),
    workflow_name="Generate Orchestrator",
    dispatch_endpoint="/actions/workflows/generate-orchestrator.yml/dispatches",
    target_sha="b" * 64,
    input_keys=("mode", "ref"),
    resolution_fingerprint="c" * 64,
)


class StubAdapter:
    def __init__(self, observation):
        self.observation = observation

    def execute(self, request):
        return self.observation


class ControlCenterWorkflowBridgeTests(unittest.TestCase):
    def command(self):
        return ControlCommand(
            command_id="CMD-GENERATE-001",
            intent="Run existing Generate Orchestrator",
            mode="LIVE",
            risk="LOW",
            target="generate-orchestrator.yml",
        )

    def observation(self, success=True):
        return WorkflowExecutionObservation(
            command_id="CMD-GENERATE-001",
            resolution_fingerprint="c" * 64,
            repository="phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH",
            workflow_file="generate-orchestrator.yml",
            run_id="9001",
            target_sha="b" * 64,
            observed_head_sha="b" * 64 if success else "d" * 64,
            status="completed",
            conclusion="success" if success else "failure",
            html_url="https://github.com/example/run/9001",
            dispatch_ref="b" * 64,
            input_keys=("mode", "ref"),
            observation_fingerprint="e" * 64,
        )

    def test_live_success_records_evidence_and_completion(self):
        control = NativeControlCenter()
        bridge = ControlCenterWorkflowBridge(control, StubAdapter(self.observation()))
        result = bridge.execute(
            command=self.command(),
            resolution=RESOLUTION,
            repository="phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH",
            target_sha="b" * 64,
            mode="LIVE",
            inputs={"mode": "inventory"},
            authorized=True,
        )
        self.assertEqual(
            result.evidence_ref,
            "github-actions://phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH/runs/9001@"
            + "b" * 64,
        )
        self.assertEqual(control.activity()[-1].state, "COMPLETE")
        self.assertEqual(control.activity()[-1].evidence_ref, result.evidence_ref)

    def test_live_failure_records_recovery(self):
        control = NativeControlCenter()
        bridge = ControlCenterWorkflowBridge(control, StubAdapter(self.observation(False)))
        result = bridge.execute(
            command=self.command(),
            resolution=RESOLUTION,
            repository="phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH",
            target_sha="b" * 64,
            mode="LIVE",
            authorized=True,
        )
        self.assertIsNotNone(result.evidence_ref)
        self.assertEqual(control.activity()[-1].state, "RECOVER")

    def test_simulation_does_not_record_live_execution(self):
        observation = WorkflowExecutionObservation(
            command_id="CMD-GENERATE-001",
            resolution_fingerprint="c" * 64,
            repository="phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH",
            workflow_file="generate-orchestrator.yml",
            run_id=None,
            target_sha="b" * 64,
            observed_head_sha=None,
            status="simulation_not_executed",
            conclusion=None,
            html_url=None,
            dispatch_ref="b" * 64,
            input_keys=(),
            observation_fingerprint="e" * 64,
        )
        control = NativeControlCenter()
        bridge = ControlCenterWorkflowBridge(control, StubAdapter(observation))
        bridge.execute(
            command=self.command(),
            resolution=RESOLUTION,
            repository="phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH",
            target_sha="b" * 64,
            mode="SIMULATION",
        )
        self.assertEqual(control.activity()[-1].state, "OBSERVE")


if __name__ == "__main__":
    unittest.main()
