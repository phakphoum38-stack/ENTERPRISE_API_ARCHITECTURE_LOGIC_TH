from __future__ import annotations

import copy
import unittest

from owner_special.research_os_friend.mission_control_evidence import (
    MissionControlEvidenceError,
    MissionControlEvidenceProjection,
)


class _Owner:
    owner_id = "owner-a"


class _Orchestrator:
    owner = _Owner()


class _Event:
    def __init__(self, sequence: int, event: str, status: str) -> None:
        self.sequence = sequence
        self.event = event
        self.status = type("Status", (), {"value": status})()


class _Run:
    def __init__(self, run_id: str, owner_id: str, status: str, evidence_id: object) -> None:
        self.run_id = run_id
        self.owner_id = owner_id
        self.status = type("Status", (), {"value": status})()
        self.response = type("Response", (), {"evidence_id": evidence_id})() if evidence_id is not None else None
        self.events = [_Event(2, "completed", status), _Event(1, "verifying", "verifying")]


class _Runtime:
    orchestrator = _Orchestrator()

    def __init__(self, runs):
        self.runs = tuple(runs)

    def list_runs(self, *, owner_id=None):
        return tuple(run for run in self.runs if run.owner_id == owner_id)


class MissionControlEvidenceProjectionTests(unittest.TestCase):
    def test_projects_existing_evidence_only(self):
        runtime = _Runtime([_Run("b", "owner-a", "completed", "e-2"), _Run("a", "owner-a", "completed", "e-1")])
        result = MissionControlEvidenceProjection(runtime).snapshot()
        self.assertEqual([item["run_id"] for item in result["records"]], ["a", "b"])
        self.assertTrue(result["read_only"])
        self.assertEqual(result["evidence_source"], "AgentRuntime")

    def test_owner_mismatch_fails_closed(self):
        runtime = _Runtime([_Run("a", "owner-b", "completed", "e-1")])
        result = MissionControlEvidenceProjection(runtime).snapshot(owner_id="owner-a")
        self.assertEqual(result["records"], [])

    def test_limit_is_bounded(self):
        runtime = _Runtime([])
        with self.assertRaises(MissionControlEvidenceError):
            MissionControlEvidenceProjection(runtime).snapshot(limit=101)

    def test_input_is_not_mutated(self):
        runtime = _Runtime([_Run("a", "owner-a", "completed", "e-1")])
        before = copy.deepcopy(runtime.runs)
        MissionControlEvidenceProjection(runtime).snapshot()
        self.assertEqual(runtime.runs[0].run_id, before[0].run_id)

    def test_secret_like_evidence_is_rejected(self):
        runtime = _Runtime([_Run("api-key", "owner-a", "completed", "e-1")])
        with self.assertRaises(MissionControlEvidenceError):
            MissionControlEvidenceProjection(runtime).snapshot()

    def test_unsupported_evidence_identifier_is_rejected(self):
        runtime = _Runtime([_Run("a", "owner-a", "completed", {"unsupported": True})])
        with self.assertRaises(MissionControlEvidenceError):
            MissionControlEvidenceProjection(runtime).snapshot()

    def test_no_execution_authority(self):
        runtime = _Runtime([])
        result = MissionControlEvidenceProjection(runtime).snapshot()
        self.assertNotIn("execute", result)
        self.assertNotIn("callback", result)
        self.assertNotIn("tool", result)


if __name__ == "__main__":
    unittest.main()
