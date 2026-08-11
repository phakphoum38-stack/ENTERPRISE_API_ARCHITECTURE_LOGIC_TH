import json
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from research_os_friend import OwnerFriendService


class OwnerFriendServiceTests(unittest.TestCase):
    def _request(self, url: str, *, owner: str | None = "owner", method: str = "GET", body: dict | None = None):
        headers = {}
        if owner is not None:
            headers["X-Research-OS-Owner"] = owner
            headers["X-Research-OS-Profile"] = "work"
            headers["X-Research-OS-Session"] = "desktop"
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
                repository_root=Path.cwd(),
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
                repository_root=Path.cwd(),
            )
            service2.start()
            try:
                _, memory2 = self._request(f"http://127.0.0.1:{service2.port}/owner/memory")
                self.assertEqual(memory2["count"], 2)
            finally:
                service2.close()

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
