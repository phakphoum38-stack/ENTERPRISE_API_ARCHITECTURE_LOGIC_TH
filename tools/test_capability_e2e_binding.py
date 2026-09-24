import tempfile
import unittest
from pathlib import Path

from tools.capability_e2e_binding import CapabilityE2EBinding
from tools.lifecycle_evidence import LifecycleEvidenceLedger

SHA = "a" * 40


class FriendExecutor:
    def __init__(self) -> None:
        self.calls = 0

    def snapshot(self) -> dict[str, object]:
        self.calls += 1
        return {"status": "ok", "read_only": True}


class MutatingExecutor:
    def __init__(self) -> None:
        self.calls = 0

    def ask(self, request: str) -> str:
        self.calls += 1
        return f"answered:{request}"


class FailingExecutor:
    def ask(self, request: str) -> str:
        raise RuntimeError("executor-failed")


def make_binding(directory: Path) -> CapabilityE2EBinding:
    return CapabilityE2EBinding(
        ledger=LifecycleEvidenceLedger(directory / "evidence.jsonl"),
        owner_id="owner-001",
        source_sha=SHA,
        target_sha=SHA,
        workflow_run_id="workflow-001",
    )


class CapabilityE2EBindingTests(unittest.TestCase):
    def test_friend_read_only_operation_reaches_existing_executor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            executor = FriendExecutor()
            result = make_binding(Path(directory)).invoke(
                capability_id="friend",
                action="inspect status",
                executor=executor,
                correlation_id="corr-friend",
                authorized=True,
            )
            self.assertEqual(result.status, "complete")
            self.assertEqual(executor.calls, 1)
            self.assertEqual(result.observation, {"status": "ok", "read_only": True})

    def test_mutation_stops_at_external_authorization_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            executor = MutatingExecutor()
            result = make_binding(Path(directory)).invoke(
                capability_id="friend",
                action="ask friend",
                executor=executor,
                args=("hello",),
                correlation_id="corr-mutation",
                authorized=False,
            )
            self.assertEqual(result.status, "recover")
            self.assertEqual(executor.calls, 0)
            self.assertIn("authorization", (result.recovery_reason or "").lower())

    def test_executor_failure_is_terminal_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            binding = make_binding(Path(directory))
            result = binding.invoke(
                capability_id="friend",
                action="ask friend",
                executor=FailingExecutor(),
                args=("hello",),
                correlation_id="corr-failure",
                authorized=True,
            )
            self.assertEqual(result.status, "recover")
            self.assertEqual(
                binding.ledger.validate_chain(
                    correlation_id="corr-failure", expected_source_sha=SHA
                ),
                (),
            )

    def test_assurance_cannot_be_promoted_to_execution(self) -> None:
        class AssuranceExecutor:
            pass

        with tempfile.TemporaryDirectory() as directory:
            result = make_binding(Path(directory)).invoke(
                capability_id="assurance",
                action="record evidence",
                executor=AssuranceExecutor(),
                correlation_id="corr-assurance",
                authorized=True,
            )
            self.assertEqual(result.status, "recover")
            self.assertIn("unsupported action", (result.recovery_reason or ""))

    def test_unknown_executor_method_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = make_binding(Path(directory)).invoke(
                capability_id="github",
                action="inspect repository",
                executor=object(),
                correlation_id="corr-github",
                authorized=True,
            )
            self.assertEqual(result.status, "recover")
            self.assertIn("canonical method", (result.recovery_reason or ""))

    def test_factory_binding_uses_existing_execute_method(self) -> None:
        class Factory:
            def execute(self, plan: str) -> str:
                return f"executed:{plan}"

        with tempfile.TemporaryDirectory() as directory:
            result = make_binding(Path(directory)).invoke(
                capability_id="factory_v3",
                action="execute factory plan",
                executor=Factory(),
                args=("plan-1",),
                correlation_id="corr-factory",
                authorized=True,
            )
            self.assertEqual(result.status, "complete")
            self.assertEqual(result.observation, "executed:plan-1")


if __name__ == "__main__":
    unittest.main()
