from __future__ import annotations

import json
import os
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from auth_session import issue_session


def _request(url: str, session: str | None = None):
    headers = {"Content-Type": "application/json"}
    if session:
        headers["X-Research-OS-Session"] = session
    request = urllib.request.Request(url, data=b"{}", headers=headers, method="POST")
    return urllib.request.urlopen(request, timeout=5)


def test_developer_assertion_endpoint_bridges_verified_session(tmp_path: Path) -> None:
    os.environ["RESEARCH_OS_SESSION_SECRET"] = "test-session-secret-012345"
    os.environ["RESEARCH_OS_V3_DATA_DIR"] = str(tmp_path)
    os.environ["RESEARCH_OS_IDENTITY_PROXY_SECRET"] = "gateway-secret-0123456789"

    from server import ResearchOSHandler
    from developer_identity import IdentityAssertionVerifier

    session = issue_session({"user_id": "owner-user-123", "email": "owner@example.test", "role": "owner"})
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), ResearchOSHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{httpd.server_port}/v1/auth/developer/assertion"
        with _request(url, session) as response:
            payload = json.loads(response.read().decode("utf-8"))

        assert payload["principal"] == "owner-user-123"
        assert payload["email"] == "owner@example.test"
        assert payload["role"] == "owner"
        assert payload["token_type"] == "research_os_developer_assertion"
        identity = IdentityAssertionVerifier("gateway-secret-0123456789").verify(
            payload["headers"],
            now=int(payload["issued_at"]) + 1,
        )
        assert identity.principal == "owner-user-123"
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)


def test_developer_assertion_endpoint_rejects_missing_session(tmp_path: Path) -> None:
    os.environ["RESEARCH_OS_SESSION_SECRET"] = "test-session-secret-012345"
    os.environ["RESEARCH_OS_V3_DATA_DIR"] = str(tmp_path)
    os.environ["RESEARCH_OS_IDENTITY_PROXY_SECRET"] = "gateway-secret-0123456789"

    from server import ResearchOSHandler

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), ResearchOSHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{httpd.server_port}/v1/auth/developer/assertion"
        try:
            _request(url)
        except urllib.error.HTTPError as exc:
            assert exc.code == 401
            return
        raise AssertionError("missing Research OS session was accepted")
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)


def test_developer_assertion_endpoint_fails_closed_without_proxy_secret(tmp_path: Path) -> None:
    os.environ["RESEARCH_OS_SESSION_SECRET"] = "test-session-secret-012345"
    os.environ["RESEARCH_OS_V3_DATA_DIR"] = str(tmp_path)
    os.environ.pop("RESEARCH_OS_IDENTITY_PROXY_SECRET", None)

    from server import ResearchOSHandler

    session = issue_session({"user_id": "owner-user-123", "email": "owner@example.test", "role": "owner"})
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), ResearchOSHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{httpd.server_port}/v1/auth/developer/assertion"
        try:
            _request(url, session)
        except urllib.error.HTTPError as exc:
            assert exc.code == 503
            return
        raise AssertionError("gateway minted an assertion without its signing secret")
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)
