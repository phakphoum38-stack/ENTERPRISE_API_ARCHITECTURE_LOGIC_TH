from __future__ import annotations

import copy
import unittest

from owner_special.research_os_friend.mission_control_unified_snapshot import (
    MissionControlUnifiedSnapshot,
    MissionControlUnifiedSnapshotError,
)


OWNER = "owner-special"


def trace(runs: list[dict[str, object]] | None = None) -> dict[str, object]:
    return {
        "schema": "research-os-mission-control/v1",
        "owner_id": OWNER,
        "read_only": True,
        "execution_authority": "FriendOrchestrator",
        "authorization_authority": "OwnerPolicy",
        "approval_authority": "ApprovalGate",
        "trace_source": "AgentRuntime",
        "runs": runs or [{"run_id": "run-002", "status": "completed"}, {"run_id": "run-001", "status": "completed"}],
        "total_runs": 2,
        "status_counts": {"completed": 2},
        "limit": 25,
    }


def timeline() -> dict[str, object]:
    return {
        "schema": "research-os-mission-control-timeline/v1",
        "run_id": "run-001",
        "owner_id": OWNER,
        "read_only": True,
        "steps": [{"sequence": 1, "event": "completed", "status": "completed"}],
        "step_count": 1,
        "truncated": False,
    }


def capabilities(rows: list[dict[str, object]] | None = None) -> dict[str, object]:
    rows = rows or [{"name": "zeta", "status": "healthy"}, {"name": "alpha", "status": "healthy"}]
    return {
        "schema": "research-os-mission-control-capabilities/v1",
        "owner_id": OWNER,
        "read_only": True,
        "execution_authority": "FriendOrchestrator",
        "authorization_authority": "OwnerPolicy",
        "approval_authority": "ApprovalGate",
        "source": "UnifiedToolCatalog+ToolHealthMatrix+ToolHealthGate",
        "total": len(rows),
        "healthy": 2,
        "counts": {"healthy": 2},
        "gate": {"passed": True},
        "rows": rows,
        "limit": 25,
        "truncated": False,
    }


def ui_schema() -> dict[str, object]:
    return {
        "schema": "research-os-mission-control-ui/v1",
        "owner_id": OWNER,
        "read_only": True,
        "execution_authority": "FriendOrchestrator",
        "authorization_authority": "OwnerPolicy",
        "approval_authority": "ApprovalGate",
        "panels": [
            {"id": "status", "type": "status", "title": "Status", "value": "PASS"},
        ],
    }


def evidence(records: list[dict[str, object]] | None = None) -> dict[str, object]:
    records = records or [{"run_id": "run-002", "status": "completed"}, {"run_id": "run-001", "status": "completed"}]
    return {
        "schema": "research-os-mission-control-evidence/v1",
        "owner_id": OWNER,
        "read_only": True,
        "evidence_source": "AgentRuntime",
        "records": records,
        "record_count": len(records),
        "total_records": len(records),
        "truncated": False,
    }


def gate_status() -> dict[str, object]:
    return {
        "schema": "research-os-mission-control-release-readiness/v1",
        "owner_id": OWNER,
        "read_only": True,
        "source_authority": "authoritative-ci-gate-evidence",
        "overall_status": "PENDING",
        "reason": "one or more required release gates are not yet passed",
        "build_identity_status": "UNKNOWN",
        "gates": {"architecture": "PASSED"},
        "authority_boundary": "projection-only; no release authority",
    }


def build_identity() -> dict[str, object]:
    return {
        "schema": "research-os-mission-control-build-identity/v1",
        "owner_id": OWNER,
        "read_only": True,
        "source_authority": "canonical-build-identity-and-installed-provenance-gates",
        "status": "VERIFIED",
        "reason": "canonical build identity and installed provenance agree",
        "identity": {"status": "VERIFIED", "file_name": "research_os_owner_special.exe"},
    }


class MissionControlUnifiedSnapshotTests(unittest.TestCase):
    def make_snapshot(self, **overrides: object) -> dict[str, object]:
        values: dict[str, object] = {
            "owner_id": OWNER,
            "trace": trace(),
            "timeline": timeline(),
            "capabilities": capabilities(),
            "ui_schema": ui_schema(),
            "evidence": evidence(),
            "gate_status": gate_status(),
            "build_identity": build_identity(),
        }
        values.update(overrides)
        return MissionControlUnifiedSnapshot().snapshot(**values)  # type: ignore[arg-type]

    def test_valid_composition(self) -> None:
        result = self.make_snapshot()
        self.assertEqual(result["schema"], MissionControlUnifiedSnapshot.SCHEMA)
        self.assertEqual(result["owner_id"], OWNER)
        self.assertIs(result["read_only"], True)
        for key in ("trace", "timeline", "capabilities", "ui_schema", "evidence", "gate_status", "build_identity"):
            self.assertIn(key, result)

    def test_owner_isolation(self) -> None:
        bad = trace()
        bad["owner_id"] = "other-owner"
        with self.assertRaises(MissionControlUnifiedSnapshotError):
            self.make_snapshot(trace=bad)

    def test_read_only_is_required(self) -> None:
        bad = gate_status()
        bad["read_only"] = False
        with self.assertRaises(MissionControlUnifiedSnapshotError):
            self.make_snapshot(gate_status=bad)

    def test_deterministic_ordering(self) -> None:
        first = self.make_snapshot()
        second = self.make_snapshot()
        self.assertEqual(first, second)
        self.assertEqual([item["run_id"] for item in first["trace"]["runs"]], ["run-001", "run-002"])  # type: ignore[index]
        self.assertEqual([item["run_id"] for item in first["evidence"]["records"]], ["run-001", "run-002"])  # type: ignore[index]
        self.assertEqual([item["name"] for item in first["capabilities"]["rows"]], ["alpha", "zeta"])  # type: ignore[index]

    def test_optional_build_identity_can_be_absent(self) -> None:
        result = self.make_snapshot(build_identity=None)
        self.assertIsNone(result["build_identity"])
        self.assertIsNone(result["source_versions"]["build_identity"])  # type: ignore[index]

    def test_truncation_is_explicit(self) -> None:
        runs = [{"run_id": f"run-{index:03d}", "status": "completed"} for index in range(3)]
        records = [{"run_id": f"run-{index:03d}", "status": "completed"} for index in range(3)]
        rows = [{"name": f"tool-{index:03d}", "status": "healthy"} for index in range(3)]
        result = self.make_snapshot(
            trace=trace(runs),
            evidence=evidence(records),
            capabilities=capabilities(rows),
            run_limit=2,
            evidence_limit=2,
            capability_limit=2,
        )
        self.assertEqual(result["truncation"], {"runs": True, "evidence": True, "capabilities": True})
        self.assertEqual(result["trace"]["returned_runs"], 2)  # type: ignore[index]
        self.assertEqual(result["evidence"]["returned_records"], 2)  # type: ignore[index]
        self.assertEqual(result["capabilities"]["returned"], 2)  # type: ignore[index]

    def test_conflicting_schema_is_rejected(self) -> None:
        bad = evidence()
        bad["schema"] = "research-os-mission-control-evidence/v999"
        with self.assertRaises(MissionControlUnifiedSnapshotError):
            self.make_snapshot(evidence=bad)

    def test_malformed_ui_schema_is_rejected(self) -> None:
        bad = ui_schema()
        bad["panels"] = [{"id": "run", "type": "execute"}]
        with self.assertRaises(MissionControlUnifiedSnapshotError):
            self.make_snapshot(ui_schema=bad)

    def test_secret_like_value_is_rejected(self) -> None:
        bad = evidence()
        bad["records"][0]["note"] = "Bearer abc123"  # type: ignore[index]
        with self.assertRaises(MissionControlUnifiedSnapshotError):
            self.make_snapshot(evidence=bad)

    def test_executable_key_is_rejected(self) -> None:
        bad = trace()
        bad["runs"][0]["command"] = "powershell -Command whoami"  # type: ignore[index]
        with self.assertRaises(MissionControlUnifiedSnapshotError):
            self.make_snapshot(trace=bad)

    def test_input_is_not_mutated(self) -> None:
        sources = {
            "trace": trace(),
            "timeline": timeline(),
            "capabilities": capabilities(),
            "ui_schema": ui_schema(),
            "evidence": evidence(),
            "gate_status": gate_status(),
            "build_identity": build_identity(),
        }
        original = copy.deepcopy(sources)
        MissionControlUnifiedSnapshot().snapshot(owner_id=OWNER, **sources)  # type: ignore[arg-type]
        self.assertEqual(sources, original)

    def test_authority_fields_cannot_be_replaced(self) -> None:
        bad = trace()
        bad["execution_authority"] = "ReleaseController"
        with self.assertRaises(MissionControlUnifiedSnapshotError):
            self.make_snapshot(trace=bad)

    def test_dynamic_values_are_rejected(self) -> None:
        bad = trace()
        bad["runs"][0]["dynamic"] = object()  # type: ignore[index]
        with self.assertRaises(MissionControlUnifiedSnapshotError):
            self.make_snapshot(trace=bad)


if __name__ == "__main__":
    unittest.main()
