import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from browser_use_cloud import BrowserUseCloudConnector, BrowserUseCloudError


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class BrowserUseCloudConnectorTest(unittest.TestCase):
    def test_status_reports_missing_backend_key_without_secret_values(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            status = BrowserUseCloudConnector(tmp).status()

        self.assertFalse(status["api_key_configured"])
        self.assertFalse(status["connected"])
        self.assertEqual(status["token_storage"], "backend_env_only")
        self.assertNotIn("api_key", status)
        self.assertNotIn("cdp_url", status)

    def test_connect_creates_cloud_browser_and_redacts_cdp_url_from_status(self):
        requests = []

        def fake_urlopen(request, timeout=0):
            requests.append(request)
            self.assertEqual(timeout, 20)
            return _Response({"id": "browser-123", "cdpUrl": "wss://cdp.browser-use.test/session-secret"})

        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {"BROWSER_USE_API_KEY": "browser-use-secret"},
            clear=True,
        ), patch("browser_use_cloud.urllib.request.urlopen", side_effect=fake_urlopen):
            connector = BrowserUseCloudConnector(tmp)
            status = connector.connect("us")

            self.assertTrue(status["connected"])
            self.assertEqual(status["browser_id"], "browser-123")
            self.assertTrue(status["cdp_url_available"])
            self.assertEqual(status["cdp_host"], "cdp.browser-use.test")
            self.assertNotIn("browser-use-secret", json.dumps(status))
            self.assertNotIn("session-secret", json.dumps(status))
            self.assertTrue((Path(tmp) / "browser_use" / "session.json").exists())

        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0].get_method(), "POST")
        self.assertEqual(requests[0].full_url, "https://api.browser-use.com/api/v4/browsers")
        self.assertEqual(requests[0].headers["X-browser-use-api-key"], "browser-use-secret")
        self.assertEqual(json.loads(requests[0].data.decode("utf-8")), {"proxyCountryCode": "us"})

    def test_disconnect_stops_existing_cloud_browser(self):
        requests = []

        def fake_urlopen(request, timeout=0):
            requests.append(request)
            return _Response({"ok": True})

        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {"BROWSER_USE_API_KEY": "browser-use-secret"},
            clear=True,
        ), patch("browser_use_cloud.urllib.request.urlopen", side_effect=fake_urlopen):
            session = Path(tmp) / "browser_use" / "session.json"
            session.parent.mkdir(parents=True, exist_ok=True)
            session.write_text(
                json.dumps({"id": "browser-123", "cdp_url": "wss://cdp.browser-use.test/session-secret"}),
                encoding="utf-8",
            )
            status = BrowserUseCloudConnector(tmp).disconnect()

        self.assertTrue(status["stopped"])
        self.assertFalse(status["connected"])
        self.assertFalse(session.exists())
        self.assertEqual(requests[0].get_method(), "PATCH")
        self.assertEqual(requests[0].full_url, "https://api.browser-use.com/api/v4/browsers/browser-123")
        self.assertEqual(json.loads(requests[0].data.decode("utf-8")), {"action": "stop"})

    def test_connect_requires_backend_key(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(BrowserUseCloudError):
                BrowserUseCloudConnector(tmp).connect()


if __name__ == "__main__":
    unittest.main()
