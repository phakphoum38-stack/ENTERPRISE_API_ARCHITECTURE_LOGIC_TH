from __future__ import annotations

import copy
import unittest

from owner_special.research_os_friend.mission_control_ui_projection import (
    MissionControlUIProjection,
    MissionControlUIProjectionError,
)


OWNER = "owner-special"


def snapshot() -> dict[str, object]:
    panels = [
        {"id": "capability", "type": "capability-health", "title": "Capability Health", "items": [{"name": "tool-a", "status": "PASS"}]},
        {"id": "metric", "type": "metric", "title": "Runs", "value": 2},
        {"id": "status", "type": "status", "title": "Status", "value": "PENDING"},
        {"id": "table", "type": "table", "title": "Evidence", "columns": ["run_id", "status"], "rows": [{"run_id": "run-001", "status": "PASS"}]},
        {"id": "text", "type": "text", "title": "Summary", "value": "Read-only"},
        {"id": "timeline", "type": "timeline", "title": "Timeline", "steps": [{"sequence": 1, "status": "PASS"}]},
    ]
    return {
        "schema": "research-os-mission-control-unified-snapshot/v1",
        "owner_id": OWNER,
        "read_only": True,
        "execution_authority": "FriendOrchestrator",
        "authorization_authority": "OwnerPolicy",
        "approval_authority": "ApprovalGate",
        "source_versions": {"trace": "research-os-mission-control/v1", "ui_schema": "research-os-mission-control-ui/v1"},
        "truncation": {"runs": False, "evidence": False, "capabilities": False},
        "ui_schema": {
            "schema": "research-os-mission-control-ui/v1",
            "owner_id": OWNER,
            "read_only": True,
            "execution_authority": "FriendOrchestrator",
            "authorization_authority": "OwnerPolicy",
            "approval_authority": "ApprovalGate",
            "panels": panels,
        },
        "trace": {"schema": "research-os-mission-control/v1", "owner_id": OWNER, "read_only": True, "runs": []},
        "timeline": {"schema": "research-os-mission-control-timeline/v1", "owner_id": OWNER, "read_only": True, "steps": []},
        "capabilities": {"schema": "research-os-mission-control-capabilities/v1", "owner_id": OWNER, "read_only": True, "rows": []},
        "evidence": {"schema": "research-os-mission-control-evidence/v1", "owner_id": OWNER, "read_only": True, "records": []},
        "gate_status": {"schema": "research-os-mission-control-release-readiness/v1", "owner_id": OWNER, "read_only": True, "overall_status": "PENDING"},
        "build_identity": None,
    }


class MissionControlUIProjectionTests(unittest.TestCase):
    def test_valid_projection(self) -> None:
        result = MissionControlUIProjection().project(snapshot(), owner_id=OWNER)
        self.assertEqual(result["schema"], MissionControlUIProjection.SCHEMA)
        self.assertEqual(result["owner_id"], OWNER)
        self.assertIs(result["read_only"], True)
        self.assertEqual(result["source_snapshot"], "research-os-mission-control-unified-snapshot/v1")

    def test_all_existing_panel_types_are_preserved(self) -> None:
        result = MissionControlUIProjection().project(snapshot(), owner_id=OWNER)
        self.assertEqual(
            {panel["type"] for panel in result["panels"]},
            {"text", "metric", "status", "table", "timeline", "capability-health"},
        )

    def test_deterministic_panel_order(self) -> None:
        first = MissionControlUIProjection().project(snapshot(), owner_id=OWNER)
        second = MissionControlUIProjection().project(snapshot(), owner_id=OWNER)
        self.assertEqual(first, second)
        self.assertEqual([panel["id"] for panel in first["panels"]], sorted(panel["id"] for panel in first["panels"]))

    def test_owner_isolation(self) -> None:
        with self.assertRaises(MissionControlUIProjectionError):
            MissionControlUIProjection().project(snapshot(), owner_id="other-owner")

    def test_snapshot_owner_mismatch_is_rejected(self) -> None:
        bad = snapshot()
        bad["owner_id"] = "other-owner"
        with self.assertRaises(MissionControlUIProjectionError):
            MissionControlUIProjection().project(bad, owner_id=OWNER)

    def test_read_only_is_required(self) -> None:
        bad = snapshot()
        bad["read_only"] = False
        with self.assertRaises(MissionControlUIProjectionError):
            MissionControlUIProjection().project(bad, owner_id=OWNER)

    def test_conflicting_snapshot_schema_is_rejected(self) -> None:
        bad = snapshot()
        bad["schema"] = "research-os-mission-control-unified-snapshot/v999"
        with self.assertRaises(MissionControlUIProjectionError):
            MissionControlUIProjection().project(bad, owner_id=OWNER)

    def test_malformed_ui_panel_is_rejected(self) -> None:
        bad = snapshot()
        bad["ui_schema"]["panels"] = [{"id": "x", "type": "execute"}]  # type: ignore[index]
        with self.assertRaises(MissionControlUIProjectionError):
            MissionControlUIProjection().project(bad, owner_id=OWNER)

    def test_secret_like_content_is_rejected(self) -> None:
        bad = snapshot()
        bad["ui_schema"]["panels"][0]["title"] = "Bearer abc123"  # type: ignore[index]
        with self.assertRaises(MissionControlUIProjectionError):
            MissionControlUIProjection().project(bad, owner_id=OWNER)

    def test_executable_content_is_rejected(self) -> None:
        bad = snapshot()
        bad["trace"]["command"] = "powershell -Command whoami"  # type: ignore[index]
        with self.assertRaises(MissionControlUIProjectionError):
            MissionControlUIProjection().project(bad, owner_id=OWNER)

    def test_dynamic_content_is_rejected(self) -> None:
        bad = snapshot()
        bad["trace"]["dynamic"] = object()  # type: ignore[index]
        with self.assertRaises(MissionControlUIProjectionError):
            MissionControlUIProjection().project(bad, owner_id=OWNER)

    def test_panel_bound_is_enforced(self) -> None:
        bad = snapshot()
        bad["ui_schema"]["panels"] = [  # type: ignore[index]
            {"id": f"panel-{index:02d}", "type": "text", "title": "x", "value": "x"}
            for index in range(33)
        ]
        with self.assertRaises(MissionControlUIProjectionError):
            MissionControlUIProjection().project(bad, owner_id=OWNER)

    def test_source_metadata_is_preserved(self) -> None:
        result = MissionControlUIProjection().project(snapshot(), owner_id=OWNER)
        self.assertEqual(result["source_versions"], snapshot()["source_versions"])
        self.assertEqual(result["truncation"], snapshot()["truncation"])

    def test_statuses_are_not_reinterpreted(self) -> None:
        source = snapshot()
        source["gate_status"]["overall_status"] = "FAILED"  # type: ignore[index]
        result = MissionControlUIProjection().project(source, owner_id=OWNER)
        self.assertEqual(result["state_summary"]["gate_status"], "FAILED")  # type: ignore[index]

    def test_input_is_not_mutated(self) -> None:
        source = snapshot()
        original = copy.deepcopy(source)
        MissionControlUIProjection().project(source, owner_id=OWNER)
        self.assertEqual(source, original)

    def test_repeated_identical_input_is_identical(self) -> None:
        source = snapshot()
        first = MissionControlUIProjection().project(source, owner_id=OWNER)
        second = MissionControlUIProjection().project(source, owner_id=OWNER)
        self.assertEqual(first, second)

    def test_authority_replacement_is_rejected(self) -> None:
        bad = snapshot()
        bad["execution_authority"] = "ReleaseController"
        with self.assertRaises(MissionControlUIProjectionError):
            MissionControlUIProjection().project(bad, owner_id=OWNER)


if __name__ == "__main__":
    unittest.main()
