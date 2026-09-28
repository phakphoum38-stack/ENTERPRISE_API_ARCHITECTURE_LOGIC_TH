import json
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from research_os_friend import OwnerFriendService


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class OwnerFriendServiceTests(unittest.TestCase):
    def _request(
        self,
        url: str,
        *,
        owner: str | None = "owner",
        profile: str = "work",
        session: str = "desktop",
        method: str = "GET",
        body: dict | None = None,
    ):
        headers = {}
        if owner is not None:
            headers["X-Research-OS-Owner"] = owner
            headers["X-Research-OS-Profile"] = profile
            headers["X-Research-OS-Session"] = session
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def test_service_chat_memory_factory_and_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            audit = root / "audit.jsonl"
            service = OwnerFriendService(
                owner_id="owner",
                port=0,
                data_root=root / "data",
                audit_path=audit,
                repository_root=REPOSITORY_ROOT,
            )
            service.start()
            base = f"http://127.0.0.1:{service.port}"
            try:
                status, health = self._request(base + "/owner/health", owner=None)
                self.assertEqual(status, 200)
                self.assertTrue(health["loopback_only"])

                status, payload = self._request(
                    base + "/owner/chat",
                    method="POST",
                    body={
                        "text": "plan owner project",
                        "complexity": 9,
                        "risk": 7,
                        "parallelism": 8,
                        "requested_skills": ["analysis", "planning", "coding", "quality"],
                    },
                )
                self.assertEqual(status, 200)
                self.assertEqual(payload["decision"]["scale"], "6^6")
                self.assertEqual(payload["decision"]["capacity"], 46656)
                self.assertEqual(payload["factory"]["stages"], ["master", "factory", "team", "tests", "release"])

                _, memory = self._request(base + "/owner/memory")
                self.assertEqual(memory["count"], 2)
                _, status_payload = self._request(base + "/owner/status")
                self.assertEqual(status_payload["memory_persistence"], "disk")
            finally:
                service.close()

            service2 = OwnerFriendService(
                owner_id="owner",
                port=0,
                data_root=root / "data",
                repository_root=REPOSITORY_ROOT,
            )
            service2.start()
            try:
                _, memory2 = self._request(f"http://127.0.0.1:{service2.port}/owner/memory")
                self.assertEqual(memory2["count"], 2)
            finally:
                service2.close()

    def test_schedule_generate_tool_routes_through_owner_chat(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = OwnerFriendService(
                owner_id="owner",
                port=0,
                data_root=root / "data",
                repository_root=REPOSITORY_ROOT,
            )
            service.start()
            base = f"http://127.0.0.1:{service.port}"

            try:
                command = {
                    "operation": "auto",
                    "month": "2026-07",
                    "schedule": {
                        "id": "owner-e2e",
                        "name": "Owner E2E July",
                    },
                    "employees": [
                        {
                            "id": "e1",
                            "employee_code": "001",
                            "first_name": "Anan",
                            "last_name": "Sukjai",
                            "nickname": "Nan",
                            "department": {
                                "id": "er",
                                "code": "ER",
                                "name": "Emergency",
                            },
                            "position": "Nurse",
                        },
                        {
                            "id": "e2",
                            "employee_code": "002",
                            "first_name": "Mali",
                            "last_name": "Dee",
                            "nickname": "Mai",
                            "department": {
                                "id": "er",
                                "code": "ER",
                                "name": "Emergency",
                            },
                            "position": "Nurse",
                        },
                    ],
                    "shift_types": [
                        {
                            "id": "day",
                            "code": "D",
                            "name": "Day",
                            "start_time": "08:00",
                            "end_time": "16:00",
                            "working_hours": 8,
                        }
                    ],
                    "coverage_requirements": [
                        {
                            "id": "r1",
                            "date": "2026-07-06",
                            "department_id": "er",
                            "shift_type_id": "day",
                            "required_employees": 2,
                        }
                    ],
                }

                status, payload = self._request(
                    base + "/owner/chat",
                    method="POST",
                    body={
                        "text": json.dumps(command),
                        "requested_tools": ["schedule.generate"],
                    },
                )

                self.assertEqual(status, 200)
                self.assertEqual(
                    payload["decision"]["tools"],
                    ["schedule.generate"],
                )
                self.assertEqual(payload["provider"], "owner-mock")
                self.assertTrue(payload["evidence_id"])

                tool_results = payload["metadata"]["tool_results"]
                self.assertIn("schedule.generate", tool_results)

                result = tool_results["schedule.generate"]
                self.assertTrue(result["completed"])
                self.assertEqual(result["assignments_created"], 2)
                self.assertEqual(result["conflicts"], [])
                self.assertEqual(result["uncovered_requirements"], [])

                assignments = []
                for day in result["schedule"]["days"].values():
                    assignments.extend(day)

                self.assertEqual(len(assignments), 2)

                # /owner/chat must create a persistent preview from the
                # exact deterministic schedule.generate result.
                preview = payload["metadata"].get("preview")
                self.assertIsInstance(preview, dict)
                self.assertTrue(preview["preview_id"])
                self.assertEqual(preview["status"], "pending")

                preview_id = preview["preview_id"]

                get_status, preview_payload = self._request(
                    base + f"/owner/schedule/previews/{preview_id}",
                    method="GET",
                )

                self.assertEqual(get_status, 200)
                self.assertEqual(preview_payload["preview_id"], preview_id)
                self.assertEqual(preview_payload["owner_id"], "owner")
                self.assertEqual(preview_payload["profile_id"], "work")
                self.assertEqual(preview_payload["session_id"], "desktop")
                self.assertEqual(preview_payload["status"], "pending")

                preview_result = preview_payload["result"]
                self.assertTrue(preview_result["completed"])
                self.assertEqual(preview_result["assignments_created"], 2)
                self.assertEqual(preview_result["conflicts"], [])
                self.assertEqual(preview_result["uncovered_requirements"], [])

                preview_assignments = []
                for day in preview_result["schedule"]["days"].values():
                    preview_assignments.extend(day)

                self.assertEqual(len(preview_assignments), 2)

                # Preview -> Confirm must preserve the exact deterministic result.
                confirm_status, confirm_payload = self._request(
                    base + f"/owner/schedule/previews/{preview_id}/confirm",
                    method="POST",
                    body={},
                )

                self.assertEqual(confirm_status, 200)
                self.assertEqual(confirm_payload["preview_id"], preview_id)
                self.assertEqual(confirm_payload["owner_id"], "owner")
                self.assertEqual(confirm_payload["profile_id"], "work")
                self.assertEqual(confirm_payload["session_id"], "desktop")
                self.assertEqual(confirm_payload["status"], "confirmed")
                self.assertEqual(
                    confirm_payload["result"],
                    preview_payload["result"],
                )

                # GET must now return confirmed.
                get_confirmed_status, confirmed_preview = self._request(
                    base + f"/owner/schedule/previews/{preview_id}",
                    method="GET",
                )

                self.assertEqual(get_confirmed_status, 200)
                self.assertEqual(confirmed_preview["status"], "confirmed")
                self.assertEqual(
                    confirmed_preview["result"],
                    preview_payload["result"],
                )

                # Confirming the same preview twice must be rejected.
                with self.assertRaises(urllib.error.HTTPError) as raised:
                    self._request(
                        base + f"/owner/schedule/previews/{preview_id}/confirm",
                        method="POST",
                        body={},
                    )

                self.assertEqual(raised.exception.code, 400)

            finally:
                service.close()

    def test_schedule_preview_confirm_respects_owner_profile_session_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            service = OwnerFriendService(
                owner_id="owner",
                port=0,
                data_root=Path(temporary),
                repository_root=REPOSITORY_ROOT,
            )
            service.start()
            base = f"http://127.0.0.1:{service.port}"

            try:
                command = {
                    "operation": "auto",
                    "month": "2026-07",
                    "schedule": {
                        "id": "scope-e2e",
                        "name": "Scope E2E July",
                    },
                    "employees": [
                        {
                            "id": "e1",
                            "employee_code": "001",
                            "first_name": "Anan",
                            "last_name": "Sukjai",
                            "department": {
                                "id": "er",
                                "code": "ER",
                                "name": "Emergency",
                            },
                            "position": "Nurse",
                        },
                        {
                            "id": "e2",
                            "employee_code": "002",
                            "first_name": "Mali",
                            "last_name": "Dee",
                            "department": {
                                "id": "er",
                                "code": "ER",
                                "name": "Emergency",
                            },
                            "position": "Nurse",
                        },
                    ],
                    "shift_types": [
                        {
                            "id": "day",
                            "code": "D",
                            "name": "Day",
                            "start_time": "08:00",
                            "end_time": "16:00",
                            "working_hours": 8,
                        }
                    ],
                    "coverage_requirements": [
                        {
                            "id": "r1",
                            "date": "2026-07-06",
                            "department_id": "er",
                            "shift_type_id": "day",
                            "required_employees": 2,
                        }
                    ],
                }

                status, payload = self._request(
                    base + "/owner/chat",
                    method="POST",
                    body={
                        "text": json.dumps(command),
                        "requested_tools": ["schedule.generate"],
                    },
                )

                self.assertEqual(status, 200)

                preview_id = payload["metadata"]["preview"]["preview_id"]

                attempts = (
                    ("other-owner", "work", "desktop"),
                    ("owner", "other-profile", "desktop"),
                    ("owner", "work", "other-session"),
                )

                for owner, profile, session in attempts:
                    with self.subTest(
                        owner=owner,
                        profile=profile,
                        session=session,
                    ):
                        with self.assertRaises(urllib.error.HTTPError) as raised:
                            self._request(
                                base + f"/owner/schedule/previews/{preview_id}/confirm",
                                owner=owner,
                                profile=profile,
                                session=session,
                                method="POST",
                                body={},
                            )

                        expected_status = 403 if owner != "owner" else 404
                        self.assertEqual(
                            raised.exception.code,
                            expected_status,
                        )

                # The original scope remains authorized.
                confirm_status, confirm_payload = self._request(
                    base + f"/owner/schedule/previews/{preview_id}/confirm",
                    owner="owner",
                    profile="work",
                    session="desktop",
                    method="POST",
                    body={},
                )

                self.assertEqual(confirm_status, 200)
                self.assertEqual(confirm_payload["status"], "confirmed")
                self.assertEqual(confirm_payload["preview_id"], preview_id)

            finally:
                service.close()

    def test_wrong_owner_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            service = OwnerFriendService(owner_id="owner", port=0, data_root=Path(temporary))
            service.start()
            try:
                request = urllib.request.Request(
                    f"http://127.0.0.1:{service.port}/owner/status",
                    headers={"X-Research-OS-Owner": "other"},
                )
                with self.assertRaises(urllib.error.HTTPError) as raised:
                    urllib.request.urlopen(request, timeout=5)
                self.assertEqual(raised.exception.code, 403)
            finally:
                service.close()

    def test_non_loopback_bind_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            OwnerFriendService(owner_id="owner", host="0.0.0.0", port=0)


if __name__ == "__main__":
    unittest.main()
