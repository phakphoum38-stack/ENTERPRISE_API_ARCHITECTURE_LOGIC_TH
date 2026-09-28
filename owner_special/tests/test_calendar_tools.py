from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from owner_special.research_os_friend.calendar_tools import calendar_health, calendar_sync, calendar_sync_status


class CalendarToolsTest(unittest.TestCase):
    def test_sync_returns_job_id_without_waiting_for_provider(self) -> None:
        with patch("owner_special.research_os_friend.calendar_tools._BRIDGE.submit_sync") as submit:
            submit.return_value.job_id = "0123456789abcdef0123456789abcdef"
            submit.return_value.operation = "sync"
            submit.return_value.status = "queued"
            payload = json.loads(calendar_sync("sync September roster"))

        self.assertEqual(payload["job_id"], "0123456789abcdef0123456789abcdef")
        self.assertEqual(payload["status"], "queued")
        self.assertIn("poll calendar.sync.status", payload["message"])

    def test_status_requires_job_id(self) -> None:
        with self.assertRaises(ValueError):
            calendar_sync_status("no job here")

    def test_health_serializes_bridge_status(self) -> None:
        with patch("owner_special.research_os_friend.calendar_tools._BRIDGE.health", return_value={"reachable": False}):
            payload = json.loads(calendar_health("health"))
        self.assertFalse(payload["reachable"])


if __name__ == "__main__":
    unittest.main()
