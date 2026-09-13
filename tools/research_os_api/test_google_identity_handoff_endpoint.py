from __future__ import annotations

import json
import os
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path


def test_google_handoff_endpoint_returns_signed_session_once(tmp_path: Path) -> None:
    os.environ["RESEARCH_OS_SESSION_SECRET"] = "test-secret-google-handoff"
    os.environ["RESEARCH_OS_V3_DATA_DIR"] = str(tmp_path)

    from auth_session import issue_session, verify_session
    from google_identity import GoogleIdentityBroker
    from oauth_handoff import create_handoff
    from server import ResearchOSHandler

    account = {"user_id": "test-user", "email": "owner@example.test", "role": "owner"}
    session = issue_session(account)
    broker = GoogleIdentityBroker(tmp_path)
    state = "test-handoff-state"
    create_handoff(broker.root, session, broker.redirect_uri(), code=state)

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), ResearchOSHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{httpd.server_port}/v1/auth/google/handoff"
        request = urllib.request.Request(url, data=b"{}", headers={"Content-Type": "application/json", "X-Research-OS-OAuth-State": state}, method="POST")
        with urllib.request.urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        assert payload["connected"] is True
        assert payload["token_type"] == "research_os_session"
        assert payload["session"] == session
        assert payload["account"]["email"] == "owner@example.test"
        assert verify_session(payload["session"])["user_id"] == "test-user"

        replay = urllib.request.Request(url, data=b"{}", headers={"Content-Type": "application/json", "X-Research-OS-OAuth-State": state}, method="POST")
        try:
            urllib.request.urlopen(replay, timeout=5)
        except urllib.error.HTTPError as exc:
            assert exc.code == 401
            return
        raise AssertionError("OAuth handoff was reusable")
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)
