import tempfile
import unittest
from pathlib import Path

from tools.lifecycle_evidence import LifecycleEvidenceLedger
from tools.project_execution import ProjectExecutionProof
from tools.project_registry import PROJECT_001, ProjectRegistry
from tools.runtime_evidence import capture_runtime_evidence

SHA = "a" * 40


class AgentExecutor:
    def run(self, request: str) -> str:
        return f"ran:{request}"


class FailingAgentExecutor:
    def run(self, request: str) -> str:
        raise RuntimeError("resource-conflict")


class ProjectExecutionTests(unittest.TestCase):
    def make_proof(self, directory: Path) -> ProjectExecutionProof:
        return ProjectExecutionProof(
            registry=ProjectRegistry((PROJECT_001,)),
            ledger=LifecycleEvidenceLedger(directory / "evidence.jsonl"),
            owner_id="owner-001",
            source_sha=SHA,
            target_sha=SHA,
            workflow_run_id="workflow-project-001",
        )

    def test_project_001_executes_through_existing_agent_executor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            proof = self.make_proof(Path(directory))
            result = proof.invoke(
                project_id="project-001",
                capability_id="agent",
                action="run agent",
                executor=AgentExecutor(),
                args=("hello",),
                correlation_id="project-001-corr-001",
                authorized=True,
            )
            self.assertEqual(result.status, "complete")
            self.assertTrue(result.evidence_valid)
            self.assertEqual(result.observation, "ran:hello")

            snapshot = capture_runtime_evidence(
                proof.ledger,
                project_id="project-001",
                correlation_id="project-001-corr-001",
                expected_source_sha=SHA,
            )
            self.assertEqual(snapshot.terminal_state, "COMPLETE")
            self.assertTrue(all(item.project_id == "project-001" for item in snapshot.records))

    def test_mutation_stops_when_authorization_is_missing(self) -> None:
        class Executor:
            def run(self, request: str) -> str:
                raise AssertionError("executor must not run")

        with tempfile.TemporaryDirectory() as directory:
            proof = self.make_proof(Path(directory))
            result = proof.invoke(
                project_id="project-001",
                capability_id="agent",
                action="run agent",
                executor=Executor(),
                args=("blocked",),
                correlation_id="project-001-corr-002",
                authorized=False,
            )
            self.assertEqual(result.status, "recover")
            self.assertIn("authorization", result.recovery_reason or "")

    def test_project_capability_boundary_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            proof = self.make_proof(Path(directory))
            with self.assertRaises(ValueError):
                proof.invoke(
                    project_id="project-001",
                    capability_id="unknown-capability",
                    action="run agent",
                    executor=AgentExecutor(),
                    correlation_id="project-001-corr-003",
                    authorized=True,
                )

    def test_executor_failure_is_terminal_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            proof = self.make_proof(Path(directory))
            result = proof.invoke(
                project_id="project-001",
                capability_id="agent",
                action="run agent",
                executor=FailingAgentExecutor(),
                args=("conflict",),
                correlation_id="project-001-corr-004",
                authorized=True,
            )
            self.assertEqual(result.status, "recover")
            self.assertEqual(
                proof.ledger.validate_chain(
                    correlation_id="project-001-corr-004",
                    expected_source_sha=SHA,
                    expected_project_id="project-001",
                ),
                (),
            )


if __name__ == "__main__":
    unittest.main()
