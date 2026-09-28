import unittest

from owner_special.research_os_friend.autobot_execution_loop import (
    AutobotExecutionError,
    ExecutionJob,
    ExecutionState,
    validate_job_payload,
)


SHA = "a" * 40
NEW_SHA = "b" * 40


class AutobotExecutionLoopTests(unittest.TestCase):
    def test_happy_path_requires_fresh_ci(self) -> None:
        job = ExecutionJob.create("job-1", "corr-1", SHA)
        for state in (
            ExecutionState.DIAGNOSING,
            ExecutionState.REPAIR_PLANNED,
            ExecutionState.REPAIRING,
            ExecutionState.LOCAL_VERIFYING,
        ):
            job = job.transition(state, "step")
        job = job.bind_repair_commit(NEW_SHA)
        job = job.transition(ExecutionState.SUBMITTED, "commit submitted")
        job = job.transition(ExecutionState.WAITING_FOR_CI, "waiting for CI")
        job = job.complete_from_ci(commit_sha=NEW_SHA, correlation_id="corr-1", ci_run_id="42", passed=True)
        self.assertEqual(job.state, ExecutionState.COMPLETED)

    def test_stale_ci_sha_is_rejected(self) -> None:
        job = ExecutionJob.create("job-2", "corr-2", SHA).bind_repair_commit(NEW_SHA)
        with self.assertRaises(AutobotExecutionError):
            job.complete_from_ci(commit_sha=SHA, correlation_id="corr-2", ci_run_id="43", passed=True)

    def test_correlation_mismatch_is_rejected(self) -> None:
        job = ExecutionJob.create("job-3", "corr-3", SHA)
        with self.assertRaises(AutobotExecutionError):
            job.complete_from_ci(commit_sha=SHA, correlation_id="other", ci_run_id="44", passed=True)

    def test_ci_failure_returns_to_diagnosis(self) -> None:
        job = ExecutionJob.create("job-4", "corr-4", SHA)
        job = job.complete_from_ci(commit_sha=SHA, correlation_id="corr-4", ci_run_id="45", passed=False)
        self.assertEqual(job.state, ExecutionState.DIAGNOSING)

    def test_invalid_transition_is_blocked(self) -> None:
        job = ExecutionJob.create("job-5", "corr-5", SHA)
        with self.assertRaises(AutobotExecutionError):
            job.transition(ExecutionState.COMPLETED, "shortcut")

    def test_repair_commit_must_differ_from_source(self) -> None:
        job = ExecutionJob.create("job-6", "corr-6", SHA)
        with self.assertRaises(AutobotExecutionError):
            job.bind_repair_commit(SHA)

    def test_failure_fingerprint_is_deterministic(self) -> None:
        left = ExecutionJob.create("job-7", "corr-7", SHA).record_failure("flutter test failed")
        right = ExecutionJob.create("job-7", "corr-7", SHA).record_failure("flutter test failed")
        self.assertEqual(left.failure_fingerprints, right.failure_fingerprints)
        self.assertEqual(left.fingerprint(), right.fingerprint())

    def test_authority_payload_is_rejected(self) -> None:
        with self.assertRaises(AutobotExecutionError):
            validate_job_payload({"action": "approve release"})

    def test_payload_is_bounded(self) -> None:
        with self.assertRaises(AutobotExecutionError):
            validate_job_payload({"summary": "x" * (64 * 1024)})


if __name__ == "__main__":
    unittest.main()
