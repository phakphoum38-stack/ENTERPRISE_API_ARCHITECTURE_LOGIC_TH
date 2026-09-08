from datetime import datetime, timezone

from reference.persistence_contract import (
    AssignmentRecord,
    AssignmentStatus,
    AttemptRecord,
    JobRecord,
    JobStatus,
    RunnerRecord,
)


def test_persistence_records_are_immutable_value_objects():
    now = datetime.now(timezone.utc)
    job = JobRecord("job-1", "wf-1", JobStatus.QUEUED, {"x": 1}, 1, now, now)
    assignment = AssignmentRecord("a-1", "job-1", "runner-a", 7, AssignmentStatus.RESERVED, None, now, now)
    runner = RunnerRecord("runner-a", "ONLINE", frozenset({"python"}), now, now)
    attempt = AttemptRecord("job-1", 1, "runner-a", "a-1", 7, now, None, "RUNNING", None)

    assert job.status is JobStatus.QUEUED
    assert assignment.fencing_token == 7
    assert "python" in runner.capabilities
    assert attempt.assignment_id == assignment.assignment_id
