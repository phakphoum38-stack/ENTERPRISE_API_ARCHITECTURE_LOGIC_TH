#!/usr/bin/env python3
import json
import unittest

from tools.workflow_execution_adapter import (
    GitHubWorkflowExecutionAdapter,
    WorkflowExecutionError,
    WorkflowExecutionRequest,
)
from tools.workflow_resolver import ResolvedWorkflow, WorkflowTarget


RESOLUTION = ResolvedWorkflow(
    command_id="CMD-GENERATE-001",
    command_fingerprint="a" * 64,
    workflow=WorkflowTarget(
        file="generate-orchestrator.yml",
        stage=100,
        role="orchestrator",
        dispatchable=False,
    ),
    workflow_name="Generate Orchestrator",
    dispatch_endpoint="/actions/workflows/generate-orchestrator.yml/dispatches",
    target_sha="b" * 64,
    input_keys=("delay_seconds", "mode", "ref"),
    resolution_fingerprint="c" * 64,
)


class FakeClock:
    def __init__(self):
        self.value = 1000.0

    def now(self):
        return self.value

    def sleep(self, seconds):
        self.value += seconds


class WorkflowExecutionAdapterTests(unittest.TestCase):
    def make_request(self, **overrides):
        values = dict(
            resolution=RESOLUTION,
            repository="phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH",
            target_sha="b" * 64,
            mode="LIVE",
            inputs={"mode": "inventory"},
            authorized=True,
            discovery_timeout_seconds=10,
            completion_timeout_seconds=20,
            poll_seconds=1,
        )
        values.update(overrides)
        return WorkflowExecutionRequest(**values)

    def test_simulation_never_calls_runner(self):
        calls = []
        adapter = GitHubWorkflowExecutionAdapter(runner=lambda *args: calls.append(args))
        observation = adapter.execute(self.make_request(mode="SIMULATION", authorized=False))
        self.assertEqual(calls, [])
        self.assertEqual(observation.status, "simulation_not_executed")
        self.assertIsNone(observation.run_id)
        self.assertEqual(len(observation.observation_fingerprint), 64)

    def test_live_requires_control_center_authorization(self):
        adapter = GitHubWorkflowExecutionAdapter(runner=lambda *args: b"")
        with self.assertRaises(WorkflowExecutionError):
            adapter.execute(self.make_request(authorized=False))

    def test_dispatch_injects_exact_ref_and_discovers_exact_head(self):
        clock = FakeClock()
        calls = []

        def runner(argv, payload):
            calls.append((list(argv), payload))
            if "dispatches" in argv[0]:
                return b""
            if "workflow_dispatch" in argv[0]:
                return json.dumps({
                    "workflow_runs": [{
                        "id": 9001,
                        "event": "workflow_dispatch",
                        "head_sha": "b" * 64,
                        "created_at": "1970-01-01T00:16:50Z",
                        "html_url": "https://github.com/example/run/9001",
                    }]
                }).encode()
            return json.dumps({
                "id": 9001,
                "status": "completed",
                "conclusion": "success",
                "head_sha": "b" * 64,
                "html_url": "https://github.com/example/run/9001",
            }).encode()

        adapter = GitHubWorkflowExecutionAdapter(
            runner=runner, now=clock.now, sleep=clock.sleep
        )
        observation = adapter.execute(self.make_request())
        self.assertEqual(observation.run_id, "9001")
        self.assertEqual(observation.conclusion, "success")
        self.assertEqual(observation.observed_head_sha, "b" * 64)
        dispatch_payload = json.loads(calls[0][1].decode())
        self.assertEqual(dispatch_payload["ref"], "b" * 64)
        self.assertEqual(dispatch_payload["inputs"]["ref"], "b" * 64)
        self.assertEqual(dispatch_payload["inputs"]["mode"], "inventory")

    def test_rejects_unknown_input(self):
        adapter = GitHubWorkflowExecutionAdapter(runner=lambda *args: b"")
        with self.assertRaises(WorkflowExecutionError):
            adapter.execute(self.make_request(inputs={"unknown": "x"}))

    def test_rejects_resolution_sha_drift(self):
        adapter = GitHubWorkflowExecutionAdapter(runner=lambda *args: b"")
        with self.assertRaises(WorkflowExecutionError):
            adapter.execute(self.make_request(
                target_sha="d" * 64,
                resolution=ResolvedWorkflow(
                    **{**RESOLUTION.__dict__, "target_sha": "b" * 64}
                ),
            ))

    def test_rejects_observed_head_sha_drift(self):
        clock = FakeClock()

        def runner(argv, payload):
            if "dispatches" in argv[0]:
                return b""
            if "workflow_dispatch" in argv[0]:
                return json.dumps({
                    "workflow_runs": [{
                        "id": 9002,
                        "event": "workflow_dispatch",
                        "head_sha": "d" * 64,
                        "created_at": "1970-01-01T00:16:50Z",
                    }]
                }).encode()
            raise AssertionError("run lookup should fail before completion")

        adapter = GitHubWorkflowExecutionAdapter(runner=runner, now=clock.now)
        with self.assertRaises(WorkflowExecutionError):
            adapter.execute(self.make_request())


if __name__ == "__main__":
    unittest.main()
