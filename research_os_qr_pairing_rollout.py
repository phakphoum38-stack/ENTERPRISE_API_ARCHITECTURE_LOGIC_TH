#!/usr/bin/env python3
"""One-pass Research OS QR pairing rollout for a local Windows clone."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import textwrap
import time
from pathlib import Path

REPO = "phakphum12345/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH"
BRANCH = "feat/qr-pairing-auth-surface"
COMMIT = "feat: replace login surface with QR pairing"


def run(cmd, cwd, check=True, capture=True):
    print("$", " ".join(cmd))
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=capture,
                          encoding="utf-8", errors="replace", check=check)


def out(cmd, cwd):
    return run(cmd, cwd).stdout.strip()


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8", newline="\n")

CONTRACT = r"""{
  "contract_id": "research-os-qr-pairing-v1",
  "version": 1,
  "status": "ACTIVE",
  "purpose": "Provide a one-time QR pairing surface that connects a trusted authenticated device to an existing Research OS session without creating a new authentication or authorization runtime.",
  "authority": {
    "identity": "tools/research_os_api/api_auth.py",
    "session": "tools/research_os_api/auth_session.py",
    "identity_context": "tools/research_os_api/identity_context.py",
    "authorization": "owner_special/research_os_friend/policy.py:OwnerPolicy",
    "provider_runtime": "tools/research_os_api/multi_login_runtime.py",
    "google_provider_runtime": "tools/research_os_api/google_identity.py",
    "handoff": "tools/research_os_api/oauth_handoff.py"
  },
  "pairing": {
    "module": "tools/research_os_api/qr_pairing.py",
    "surface": "apps/research_os_flutter/lib/src/features/auth/login_page.dart",
    "states": ["PENDING", "SCANNED", "CONNECTED", "EXPIRED", "CANCELLED"],
    "ttl_seconds": 180,
    "single_use": true,
    "qr_payload": "one-time HTTPS pairing URL",
    "must_not_contain": ["password", "research_os_session", "provider access token", "refresh token", "role grant", "permission grant"]
  },
  "runtime_rules": {
    "new_auth_runtime": false,
    "new_session_authority": false,
    "new_authorization_authority": false,
    "new_navigation_registry": false,
    "provider_identity_remains_server_derived": true,
    "role_remains_server_derived": true,
    "authorization_remains_server_derived": true,
    "qr_is_pairing_only": true
  },
  "security": {
    "secret_storage": "SHA-256 hash at rest; transient raw secret only while binding OAuth state",
    "replay": "deny after handoff consume",
    "expiration": "deny after TTL",
    "session_delivery": "existing one-time oauth_handoff",
    "session_never_encoded_in_qr": true,
    "fail_closed": true
  },
  "verification": {
    "python_test": "tools/research_os_api/test_qr_pairing.py",
    "flutter_test": "apps/research_os_flutter/test/login_page_test.dart",
    "m2_audit": "tools/research_os_m2_audit.py",
    "release_authority": "FINAL_GATE"
  }
}"""

QR_MODULE = r"""from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path
from threading import Lock
from typing import Any

PAIRING_TTL_SECONDS = 180
STATE_SCHEMA = "RESEARCH_OS_QR_PAIRING_V1"
_FILENAME = "qr_pairings.json"
_LOCK = Lock()


class QRPairingError(ValueError):
    # Invalid, expired, cancelled, or already-consumed pairing.


def _root() -> Path:
    configured = (os.getenv("RESEARCH_OS_DATA_DIR") or "").strip()
    if configured:
        root = Path(configured).expanduser()
    else:
        try:
            from google_identity import GoogleIdentityBroker
        except ImportError:
            from .google_identity import GoogleIdentityBroker
        root = GoogleIdentityBroker().root
    root.mkdir(parents=True, exist_ok=True)
    return root


def _path() -> Path:
    return _root() / _FILENAME


def _digest(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def _read() -> dict[str, Any]:
    path = _path()
    try:
        value = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, ValueError, TypeError):
        return {}
    if not isinstance(value, dict) or value.get("schema") != STATE_SCHEMA:
        return {"schema": STATE_SCHEMA, "pairings": {}}
    pairings = value.get("pairings")
    return {"schema": STATE_SCHEMA, "pairings": pairings if isinstance(pairings, dict) else {}}


def _write(value: dict[str, Any]) -> None:
    path = _path()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass
    os.replace(tmp, path)


def _prune(pairings: dict[str, Any], now: int) -> None:
    for record in pairings.values():
        if not isinstance(record, dict):
            continue
        if int(record.get("expires_at", 0)) <= now and record.get("status") not in {"CONNECTED", "CANCELLED", "EXPIRED"}:
            record["status"] = "EXPIRED"
            record.pop("oauth_state", None)
            record.pop("_pending_secret", None)


def create_pairing() -> dict[str, Any]:
    now = int(time.time())
    pairing_id = secrets.token_urlsafe(18)
    secret = secrets.token_urlsafe(32)
    record = {
        "pairing_id": pairing_id,
        "secret_hash": _digest(secret),
        "created_at": now,
        "expires_at": now + PAIRING_TTL_SECONDS,
        "status": "PENDING",
    }
    with _LOCK:
        state = _read()
        _prune(state["pairings"], now)
        state["pairings"][pairing_id] = record
        _write(state)
    return {"pairing_id": pairing_id, "pairing_secret": secret, "expires_at": record["expires_at"], "status": record["status"]}


def _validated(pairing_id: str, secret: str):
    pid = str(pairing_id or "").strip()
    supplied = str(secret or "").strip()
    if not pid or not supplied:
        raise QRPairingError("pairing_id and pairing_secret are required")
    with _LOCK:
        state = _read()
        now = int(time.time())
        _prune(state["pairings"], now)
        record = state["pairings"].get(pid)
        if not isinstance(record, dict):
            _write(state)
            raise QRPairingError("pairing is missing or expired")
        expected = str(record.get("secret_hash") or "")
        if not expected or not hmac.compare_digest(expected, _digest(supplied)):
            _write(state)
            raise QRPairingError("pairing secret is invalid")
        if int(record.get("expires_at", 0)) <= now and record.get("status") != "CONNECTED":
            record["status"] = "EXPIRED"
            _write(state)
            raise QRPairingError("pairing is expired")
        if record.get("status") == "CANCELLED":
            _write(state)
            raise QRPairingError("pairing is cancelled")
        _write(state)
        return state, record


def get_status(pairing_id: str, secret: str) -> dict[str, Any]:
    _, record = _validated(pairing_id, secret)
    account = record.get("account") if isinstance(record.get("account"), dict) else None
    return {
        "pairing_id": record["pairing_id"],
        "status": record["status"],
        "expires_at": record["expires_at"],
        "connected": record["status"] == "CONNECTED",
        "handoff_ready": record["status"] == "CONNECTED",
        "account": account,
    }


def bind_oauth_state(pairing_id: str, secret: str, oauth_state: str, provider: str) -> None:
    state, record = _validated(pairing_id, secret)
    value = str(oauth_state or "").strip()
    if not value:
        raise QRPairingError("oauth state is required")
    if record.get("status") not in {"PENDING", "SCANNED"}:
        raise QRPairingError("pairing is not available")
    record["status"] = "SCANNED"
    record["oauth_state"] = value
    record["provider"] = str(provider or "").strip().lower()
    record["_pending_secret"] = secret
    _write(state)


def consume_oauth_binding(oauth_state: str) -> dict[str, str] | None:
    wanted = str(oauth_state or "").strip()
    if not wanted:
        return None
    with _LOCK:
        state = _read()
        _prune(state["pairings"], int(time.time()))
        for record in state["pairings"].values():
            if not isinstance(record, dict):
                continue
            candidate = str(record.get("oauth_state") or "")
            if candidate and hmac.compare_digest(candidate, wanted):
                secret = str(record.pop("_pending_secret", "") or "")
                pairing_id = str(record.get("pairing_id") or "")
                record.pop("oauth_state", None)
                if not secret or not pairing_id:
                    _write(state)
                    raise QRPairingError("pairing binding is incomplete")
                _write(state)
                return {"pairing_id": pairing_id, "pairing_secret": secret, "provider": str(record.get("provider") or "")}
        _write(state)
    return None


def complete_pairing(pairing_id: str, *, provider: str, account: dict[str, Any] | None) -> None:
    pid = str(pairing_id or "").strip()
    with _LOCK:
        state = _read()
        record = state["pairings"].get(pid)
        if not isinstance(record, dict):
            raise QRPairingError("pairing is missing")
        if int(record.get("expires_at", 0)) <= int(time.time()):
            record["status"] = "EXPIRED"
            _write(state)
            raise QRPairingError("pairing expired before completion")
        record["status"] = "CONNECTED"
        record["connected_at"] = int(time.time())
        record["provider"] = str(provider or "").strip().lower()
        if isinstance(account, dict):
            record["account"] = {
                "user_id": str(account.get("user_id") or account.get("sub") or "").strip(),
                "email": str(account.get("email") or "").strip(),
                "role": str(account.get("role") or "").strip().lower(),
            }
        record.pop("oauth_state", None)
        record.pop("_pending_secret", None)
        _write(state)


def cancel_pairing(pairing_id: str, secret: str) -> dict[str, Any]:
    state, record = _validated(pairing_id, secret)
    record["status"] = "CANCELLED"
    record.pop("oauth_state", None)
    record.pop("_pending_secret", None)
    _write(state)
    return {"pairing_id": record["pairing_id"], "status": record["status"], "cancelled": True}
"""

TEST_QR = r"""from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

import qr_pairing


class QRPairingTests(unittest.TestCase):
    def setUp(self):
        self.data = tempfile.TemporaryDirectory()
        self.prev = os.environ.get("RESEARCH_OS_DATA_DIR")
        os.environ["RESEARCH_OS_DATA_DIR"] = self.data.name

    def tearDown(self):
        if self.prev is None:
            os.environ.pop("RESEARCH_OS_DATA_DIR", None)
        else:
            os.environ["RESEARCH_OS_DATA_DIR"] = self.prev
        self.data.cleanup()

    def test_secret_is_hashed_at_rest(self):
        created = qr_pairing.create_pairing()
        raw = Path(self.data.name, "qr_pairings.json").read_text(encoding="utf-8")
        self.assertNotIn(created["pairing_secret"], raw)
        self.assertEqual(qr_pairing.get_status(created["pairing_id"], created["pairing_secret"])["status"], "PENDING")

    def test_invalid_secret_fails_closed(self):
        created = qr_pairing.create_pairing()
        with self.assertRaises(qr_pairing.QRPairingError):
            qr_pairing.get_status(created["pairing_id"], "wrong")

    def test_oauth_binding_is_single_use(self):
        created = qr_pairing.create_pairing()
        qr_pairing.bind_oauth_state(created["pairing_id"], created["pairing_secret"], "oauth-state", "github")
        binding = qr_pairing.consume_oauth_binding("oauth-state")
        self.assertEqual(binding["pairing_id"], created["pairing_id"])
        self.assertEqual(binding["pairing_secret"], created["pairing_secret"])
        self.assertIsNone(qr_pairing.consume_oauth_binding("oauth-state"))

    def test_completed_pairing_never_persists_session(self):
        created = qr_pairing.create_pairing()
        qr_pairing.complete_pairing(
            created["pairing_id"],
            provider="github",
            account={"user_id": "github:123", "email": "owner@example.com", "role": "OWNER", "session": "SECRET"},
        )
        raw = Path(self.data.name, "qr_pairings.json").read_text(encoding="utf-8")
        self.assertNotIn("SECRET", raw)
        self.assertTrue(qr_pairing.get_status(created["pairing_id"], created["pairing_secret"])["connected"])


if __name__ == "__main__":
    unittest.main()
"""

SERVER_AUTH = r"""from __future__ import annotations

from http.cookies import CookieError, SimpleCookie
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from auth_session import SESSION_COOKIE, clear_cookie_header, cookie_header, revoke_session, verify_session
from google_identity import GoogleIdentityBroker
from multi_login_runtime import MultiLoginRuntimeError, begin_runtime_login, complete_runtime_login
from oauth_handoff import consume_handoff, create_handoff
from qr_pairing import QRPairingError, bind_oauth_state, complete_pairing, consume_oauth_binding


def _session_token(cookie_header_value: str | None) -> str:
    if not cookie_header_value:
        return ""
    cookie = SimpleCookie()
    try:
        cookie.load(cookie_header_value)
    except (CookieError, ValueError):
        return ""
    morsel = cookie.get(SESSION_COOKIE)
    return morsel.value if morsel is not None else ""


def auth_provider_login(provider: str, redirect_uri: str) -> dict:
    _, authorization_url = begin_runtime_login(provider, redirect_uri)
    return {"authorization_url": authorization_url, "redirect_uri": redirect_uri, "token_storage": "backend_only"}


def _pairing_completion(state: str, result: dict) -> dict | None:
    binding = consume_oauth_binding(state)
    if binding is None:
        return None
    session = str(result.get("session") or "").strip()
    if not session:
        raise MultiLoginRuntimeError("pairing authentication did not produce a Research OS session")
    provider = str(result.get("provider") or binding.get("provider") or "").strip().lower()
    account = result.get("principal") if isinstance(result.get("principal"), dict) else result.get("account") if isinstance(result.get("account"), dict) else {}
    create_handoff(Path(__file__).resolve().parents[2], session, "", code=binding["pairing_secret"])
    complete_pairing(binding["pairing_id"], provider=provider, account=account)
    return {"pairing_id": binding["pairing_id"], "paired": True, "provider": provider}


def auth_callback(provider: str, query: str) -> tuple[dict, str]:
    values = parse_qs(urlparse("?" + query).query)
    error = values.get("error", [None])[0]
    if error:
        raise MultiLoginRuntimeError(f"identity provider returned error: {error}")
    code = values.get("code", [None])[0]
    state = values.get("state", [None])[0]
    if not code or not state:
        raise MultiLoginRuntimeError("OAuth callback requires code and state")
    result = complete_runtime_login(code, state)
    session = str(result.get("session") or "").strip()
    if not session:
        raise MultiLoginRuntimeError("identity provider login did not produce a Research OS session")
    pairing = _pairing_completion(state, result)
    if pairing is None:
        create_handoff(Path(__file__).resolve().parents[2], session, "", code=state)
    else:
        result["pairing"] = pairing
    return result, result["set_cookie"]


def google_auth_callback(query: str) -> tuple[dict, str]:
    values = parse_qs(urlparse("?" + query).query)
    error = str(values.get("error", [""])[0]).strip()
    if error:
        raise MultiLoginRuntimeError(f"identity provider returned error: {error}")
    code = str(values.get("code", [""])[0]).strip()
    state = str(values.get("state", [""])[0]).strip()
    if not code or not state:
        raise MultiLoginRuntimeError("Google OAuth callback requires code and state")
    result = GoogleIdentityBroker().complete(code=code, state=state)
    session = str(result.get("session") or "").strip()
    if not session:
        raise MultiLoginRuntimeError("Google OAuth completion did not produce a Research OS session")
    account = result.get("account") if isinstance(result.get("account"), dict) else {}
    pairing = _pairing_completion(state, {"session": session, "provider": "google", "account": account})
    payload = {"provider": "google", "account": account, "session": session}
    if pairing is not None:
        payload["pairing"] = pairing
    return payload, cookie_header(session, secure=True)


def auth_status(cookie_header_value: str | None) -> dict:
    token = _session_token(cookie_header_value)
    if not token:
        return {"connected": False, "account": None}
    try:
        session = verify_session(token)
    except ValueError:
        return {"connected": False, "account": None}
    return {"connected": True, "account": {"user_id": session["user_id"], "email": session["email"], "role": session["role"]}}


def auth_signout(cookie_header_value: str | None) -> str:
    token = _session_token(cookie_header_value)
    if token:
        try:
            revoke_session(token)
        except ValueError:
            pass
    return clear_cookie_header()


def auth_provider_handoff(state: str) -> dict:
    handoff = str(state or "").strip()
    if not handoff:
        raise MultiLoginRuntimeError("OAuth handoff state is required")
    session = consume_handoff(Path(__file__).resolve().parents[2], handoff)
    if not session:
        raise MultiLoginRuntimeError("OAuth handoff is missing, expired, or already consumed")
    principal = verify_session(session)
    return {"connected": True, "session": session, "account": {"user_id": principal["user_id"], "email": principal["email"], "role": principal["role"]}, "token_type": "research_os_session"}


def auth_pairing_authorize(provider: str, pairing_id: str, pairing_secret: str, redirect_uri: str) -> str:
    provider_name = str(provider or "").strip().lower()
    if provider_name == "google":
        result = GoogleIdentityBroker().begin()
        state = str(result.get("state") or "").strip()
        authorization_url = str(result.get("authorization_url") or "").strip()
    else:
        state, authorization_url = begin_runtime_login(provider_name, redirect_uri)
    if not state or not authorization_url:
        raise MultiLoginRuntimeError("pairing provider authorization could not be started")
    bind_oauth_state(pairing_id, pairing_secret, state, provider_name)
    return authorization_url
"""

LOGIN_PAGE = r"""import 'dart:async';

import 'package:flutter/material.dart';
import 'package:qr_flutter/qr_flutter.dart';

import '../../api/api_endpoint_store.dart';
import '../../api/research_os_api_client.dart';

class LoginPage extends StatefulWidget {
  const LoginPage({
    required this.apiClient,
    required this.onAuthenticated,
    required this.onConnectionChanged,
    required this.connectionProfile,
    super.key,
  });

  final ResearchOSApiClient apiClient;
  final VoidCallback onAuthenticated;
  final Future<void> Function(String baseUrl) onConnectionChanged;
  final String connectionProfile;

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  bool _loading = true;
  bool _error = false;
  String? _message;
  String? _pairingId;
  String? _pairingSecret;
  String? _qrPayload;
  Timer? _pollTimer;
  bool _refreshing = false;
  String _selectedPort = ApiEndpointStore.port1Label;

  @override
  void initState() {
    super.initState();
    final currentProfile = ApiEndpointStore.profileForUrl(widget.apiClient.baseUrl);
    _selectedPort = currentProfile == ApiEndpointStore.connectionOwnerSpecial
        ? ApiEndpointStore.port2Label
        : ApiEndpointStore.port1Label;
    _startPairing();
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  Future<void> _selectPort(String label) async {
    final profile = ApiEndpointStore.profileForPortLabel(label);
    final currentProfile = ApiEndpointStore.profileForUrl(widget.apiClient.baseUrl);
    if (profile == currentProfile) {
      if (mounted) setState(() => _selectedPort = label);
      return;
    }
    setState(() => _refreshing = true);
    try {
      await widget.onConnectionChanged(ApiEndpointStore.profileUrl(profile));
      if (!mounted) return;
      setState(() => _selectedPort = label);
      await _startPairing();
    } finally {
      if (mounted) setState(() => _refreshing = false);
    }
  }

  Future<void> _startPairing() async {
    _pollTimer?.cancel();
    if (mounted) {
      setState(() {
        _loading = true;
        _refreshing = true;
        _error = false;
        _message = null;
        _pairingId = null;
        _pairingSecret = null;
        _qrPayload = null;
      });
    }
    try {
      final result = await widget.apiClient.startPairing();
      final id = result['pairing_id']?.toString().trim() ?? '';
      final secret = result['pairing_secret']?.toString().trim() ?? '';
      final payload = result['qr_payload']?.toString().trim() ?? '';
      if (id.isEmpty || secret.isEmpty || payload.isEmpty) {
        throw const ResearchOSApiException('Research OS did not return a valid QR pairing payload.');
      }
      if (!mounted) return;
      setState(() {
        _loading = false;
        _refreshing = false;
        _pairingId = id;
        _pairingSecret = secret;
        _qrPayload = payload;
        _message = 'Scan this QR code with a trusted device.';
      });
      unawaited(_pollPairing());
    } on Object catch (error) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _refreshing = false;
        _error = true;
        _message = error.toString();
      });
    }
  }

  Future<void> _pollPairing() async {
    final pairingId = _pairingId;
    final secret = _pairingSecret;
    if (pairingId == null || secret == null) return;

    for (var attempt = 0; attempt < 180; attempt++) {
      if (!mounted) return;
      try {
        final status = await widget.apiClient.getPairingStatus(pairingId, secret);
        if (status['connected'] == true && status['handoff_ready'] == true) {
          final result = await widget.apiClient.exchangeProviderHandoff(secret);
          final session = result['session']?.toString().trim() ?? '';
          if (result['connected'] == true && session.isNotEmpty) {
            widget.apiClient.setSession(session);
            if (!mounted) return;
            setState(() {
              _error = false;
              _message = 'Connected';
            });
            widget.onAuthenticated();
            return;
          }
          throw const ResearchOSApiException('Research OS did not return a valid session handoff.');
        }
        final statusName = status['status']?.toString() ?? 'PENDING';
        if (statusName == 'EXPIRED' || statusName == 'CANCELLED') {
          if (!mounted) return;
          setState(() {
            _error = true;
            _message = 'QR pairing $statusName. Refresh the QR code and try again.';
          });
          return;
        }
      } on ResearchOSApiException {
        // The pairing remains pending or a one-time handoff race is still settling.
      } on Object catch (error) {
        if (!mounted) return;
        setState(() {
          _error = true;
          _message = error.toString();
        });
        return;
      }
      await Future<void>.delayed(const Duration(seconds: 1));
    }

    if (mounted) {
      setState(() {
        _error = true;
        _message = 'QR pairing expired. Refresh the QR code and try again.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(vertical: 24),
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 560),
              child: Padding(
                padding: const EdgeInsets.all(28),
                child: Card(
                  child: Padding(
                    padding: const EdgeInsets.all(30),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: <Widget>[
                        Icon(Icons.qr_code_2, size: 64, color: scheme.primary),
                        const SizedBox(height: 18),
                        Text(
                          'Research OS',
                          textAlign: TextAlign.center,
                          style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w800),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Scan to Connect',
                          textAlign: TextAlign.center,
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        const SizedBox(height: 24),
                        const Text('PORT', style: TextStyle(fontWeight: FontWeight.w700)),
                        const SizedBox(height: 8),
                        DropdownButtonFormField<String>(
                          key: const ValueKey('login-port-dropdown'),
                          initialValue: _selectedPort,
                          decoration: const InputDecoration(border: OutlineInputBorder()),
                          items: const <DropdownMenuItem<String>>[
                            DropdownMenuItem<String>(value: ApiEndpointStore.port1Label, child: Text(ApiEndpointStore.port1Label)),
                            DropdownMenuItem<String>(value: ApiEndpointStore.port2Label, child: Text(ApiEndpointStore.port2Label)),
                          ],
                          onChanged: _refreshing ? null : (value) {
                            if (value != null) _selectPort(value);
                          },
                        ),
                        const SizedBox(height: 24),
                        if (_qrPayload != null)
                          Center(
                            child: Semantics(
                              label: 'Research OS QR pairing code',
                              child: Container(
                                padding: const EdgeInsets.all(12),
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  borderRadius: BorderRadius.circular(16),
                                ),
                                child: QrImageView(
                                  data: _qrPayload!,
                                  version: QrVersions.auto,
                                  size: 260,
                                  gapless: false,
                                  backgroundColor: Colors.white,
                                ),
                              ),
                            ),
                          )
                        else
                          const Center(child: SizedBox(width: 48, height: 48, child: CircularProgressIndicator())),
                        const SizedBox(height: 20),
                        Text(
                          _loading ? 'Creating a secure pairing code…' : 'Scan this code with your trusted device.',
                          textAlign: TextAlign.center,
                        ),
                        if (_message != null) ...<Widget>[
                          const SizedBox(height: 12),
                          Text(
                            _message!,
                            textAlign: TextAlign.center,
                            style: TextStyle(color: _error ? scheme.error : scheme.primary),
                          ),
                        ],
                        const SizedBox(height: 22),
                        OutlinedButton.icon(
                          key: const ValueKey('refresh-qr-button'),
                          onPressed: _refreshing ? null : _startPairing,
                          icon: const Icon(Icons.refresh),
                          label: const Text('Refresh QR'),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
"""

LOGIN_TEST = r"""import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:research_os_flutter/src/api/research_os_api_client.dart';
import 'package:research_os_flutter/src/features/auth/login_page.dart';

void main() {
  testWidgets('shared auth surface uses QR pairing instead of login choices', (tester) async {
    var authenticated = 0;
    final client = ResearchOSApiClient(
      baseUrl: 'http://research-os.test',
      client: MockClient((request) async {
        switch (request.url.path) {
          case '/v1/auth/pairing/start':
            return http.Response(
              jsonEncode({
                'pairing_id': 'pair-123',
                'pairing_secret': 'secret-123',
                'expires_at': 9999999999,
                'status': 'PENDING',
                'qr_payload': 'https://research-os.test/v1/auth/pairing/open?pairing_id=pair-123&secret=secret-123',
              }),
              201,
              headers: {'content-type': 'application/json'},
            );
          case '/v1/auth/pairing/status':
            return http.Response(
              jsonEncode({
                'pairing_id': 'pair-123',
                'status': 'CONNECTED',
                'expires_at': 9999999999,
                'connected': true,
                'handoff_ready': true,
                'account': {'user_id': 'github:123', 'email': 'owner@example.com', 'role': 'owner'},
              }),
              200,
              headers: {'content-type': 'application/json'},
            );
          case '/v1/auth/providers/handoff':
            expect(request.headers['x-research-os-oauth-state'], 'secret-123');
            return http.Response(
              jsonEncode({'connected': true, 'session': 'session-token'}),
              200,
              headers: {'content-type': 'application/json'},
            );
          default:
            fail('Unexpected request: ${request.method} ${request.url}');
        }
      }),
    );
    addTearDown(client.close);
    await tester.pumpWidget(
      MaterialApp(
        home: LoginPage(
          apiClient: client,
          connectionProfile: 'research_os',
          onConnectionChanged: (_) async {},
          onAuthenticated: () => authenticated++,
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('Research OS'), findsOneWidget);
    expect(find.text('Scan to Connect'), findsOneWidget);
    expect(find.text('PORT'), findsOneWidget);
    expect(find.text('PORT 1'), findsOneWidget);
    expect(find.byKey(const ValueKey('refresh-qr-button')), findsOneWidget);
    expect(find.text('LOGIN'), findsNothing);
    expect(find.text('Select Login Method'), findsNothing);
    expect(find.text('USER LEVEL'), findsNothing);
    expect(find.text('Windows'), findsNothing);
    expect(find.text('GitHub'), findsNothing);
    expect(find.text('Google'), findsNothing);
    expect(find.text('None'), findsNothing);
    expect(find.text('Custom'), findsNothing);
    expect(authenticated, 1);
  });
}
"""


def patch_server(path: Path):
    s = path.read_text(encoding="utf-8")
    if "import html\n" not in s:
        s = s.replace("import importlib.util\n", "import importlib.util\nimport html\n", 1)
    s = s.replace(
        "from server_auth_routes import auth_provider_handoff\n",
        "from server_auth_routes import auth_pairing_authorize, auth_provider_handoff\n",
        1,
    )
    if "from qr_pairing import QRPairingError" not in s:
        s = s.replace(
            "from oauth_handoff import consume_handoff\n",
            "from oauth_handoff import consume_handoff\nfrom qr_pairing import QRPairingError, cancel_pairing, create_pairing, get_status\n",
            1,
        )
    if "def _pairing_base_url" not in s:
        marker = "    def _auth_status(self) -> dict[str, Any]:\n"
        helper = '''    def _pairing_base_url(self) -> str:\n        explicit = (\n            os.getenv("RESEARCH_OS_PAIRING_BASE_URL")\n            or os.getenv("RESEARCH_OS_PUBLIC_BASE_URL")\n            or os.getenv("RENDER_EXTERNAL_URL")\n        )\n        if explicit and explicit.strip():\n            return explicit.strip().rstrip("/")\n        host = str(self.headers.get("Host") or "").strip()\n        if host:\n            return f"http://{host.rstrip('/')}"\n        port = int(os.getenv("RESEARCH_OS_API_PORT", "8787"))\n        return f"http://127.0.0.1:{port}"\n\n'''
        s = s.replace(marker, helper + marker, 1)
    get_marker = '''            if path == "/v1/auth/providers":\n                self._send(HTTPStatus.OK, {"providers": provider_catalog()})\n                return\n'''
    get_block = '''            if path == "/v1/auth/pairing/status":\n                params = parse_qs(parsed.query)\n                self._send(HTTPStatus.OK, get_status(\n                    str(params.get("pairing_id", [""])[0]).strip(),\n                    str(params.get("secret", [""])[0]).strip(),\n                ))\n                return\n            if path == "/v1/auth/pairing/open":\n                params = parse_qs(parsed.query)\n                pairing_id = str(params.get("pairing_id", [""])[0]).strip()\n                secret = str(params.get("secret", [""])[0]).strip()\n                get_status(pairing_id, secret)\n                buttons = []\n                for item in provider_catalog():\n                    if not isinstance(item, dict) or item.get("available") is not True:\n                        continue\n                    provider = html.escape(str(item.get("id") or "").strip(), quote=True)\n                    name = html.escape(str(item.get("name") or provider), quote=True)\n                    pid = html.escape(pairing_id, quote=True)\n                    sec = html.escape(secret, quote=True)\n                    href = f"/v1/auth/pairing/authorize?provider={provider}&pairing_id={pid}&secret={sec}"\n                    buttons.append(f'<p><a href="{href}" style="display:inline-block;padding:12px 18px;border:1px solid #888;border-radius:8px;text-decoration:none">{name}</a></p>')\n                body = (\n                    "<html><head><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"\n                    "<title>Research OS Connect</title></head><body style=\"font-family:system-ui;max-width:520px;margin:48px auto;padding:20px\">"\n                    "<h2>Research OS</h2><p>Choose the identity provider for this pairing.</p>"\n                    + "".join(buttons)\n                    + "<p>This pairing is single-use and expires automatically.</p></body></html>"\n                )\n                self._send_html(HTTPStatus.OK, body)\n                return\n            if path == "/v1/auth/pairing/authorize":\n                params = parse_qs(parsed.query)\n                provider = str(params.get("provider", [""])[0]).strip().lower()\n                pairing_id = str(params.get("pairing_id", [""])[0]).strip()\n                secret = str(params.get("secret", [""])[0]).strip()\n                authorization_url = auth_pairing_authorize(\n                    provider, pairing_id, secret, self._multi_login_redirect(provider)\n                )\n                self._redirect(authorization_url)\n                return\n'''
    if "/v1/auth/pairing/open" not in s:
        s = s.replace(get_marker, get_marker + get_block, 1)
    google_old = '''            if path == "/v1/auth/google/callback":\n                params = parse_qs(parsed.query)\n                error = str(params.get("error", [""])[0]).strip()\n                if error:\n                    self._send_html(HTTPStatus.BAD_REQUEST, f"<html><body><h2>Research OS Google sign-in failed</h2><p>{error}</p><p>You can close this window.</p></body></html>")\n                    return\n                code = str(params.get("code", [""])[0]).strip()\n                state = str(params.get("state", [""])[0]).strip()\n                if not code or not state:\n                    raise ValueError("Google sign-in callback requires code and state")\n                result = GoogleIdentityBroker().complete(code=code, state=state)\n                email = ((result.get("account") or {}).get("email") or "Google account")\n                self._send_html(HTTPStatus.OK, f"<html><body><h2>Signed in to Research OS</h2><p>{email}</p><p>You can close this window.</p></body></html>")\n                return\n'''
    google_new = '''            if path == "/v1/auth/google/callback":\n                from server_auth_routes import google_auth_callback\n                result, cookie = google_auth_callback(parsed.query)\n                pairing = result.get("pairing") if isinstance(result, dict) else None\n                account = result.get("account") if isinstance(result.get("account"), dict) else {}\n                email = html.escape(str(account.get("email") or "account"), quote=True)\n                if pairing:\n                    self._send_html(HTTPStatus.OK, f"<html><body><h2>Research OS pairing complete</h2><p>{email}</p><p>You can close this window and return to Research OS.</p></body></html>")\n                else:\n                    self._send_html(HTTPStatus.OK, f"<html><body><h2>Signed in to Research OS</h2><p>{email}</p><p>You can close this window.</p></body></html>")\n                return\n'''
    if google_old in s:
        s = s.replace(google_old, google_new, 1)
    generic_old = '''                    result, cookie = __import__("server_auth_routes").auth_callback(provider, parsed.query)\n                    self._redirect("/", cookie)\n                    return\n'''
    generic_new = '''                    result, cookie = __import__("server_auth_routes").auth_callback(provider, parsed.query)\n                    pairing = result.get("pairing") if isinstance(result, dict) else None\n                    if pairing:\n                        account = result.get("principal") if isinstance(result.get("principal"), dict) else {}\n                        email = html.escape(str(account.get("email") or "account"), quote=True)\n                        self._send_html(HTTPStatus.OK, f"<html><body><h2>Research OS pairing complete</h2><p>{email}</p><p>You can close this window and return to Research OS.</p></body></html>")\n                    else:\n                        self._redirect("/", cookie)\n                    return\n'''
    if generic_old in s:
        s = s.replace(generic_old, generic_new, 1)
    post_marker = '''            if path == "/v1/auth/providers/login":\n'''
    post_block = '''            if path == "/v1/auth/pairing/start":\n                pairing = create_pairing()\n                pairing_url = f"{self._pairing_base_url()}/v1/auth/pairing/open?pairing_id={pairing['pairing_id']}&secret={pairing['pairing_secret']}"\n                self._send(HTTPStatus.CREATED, {**pairing, "qr_payload": pairing_url, "pairing_url": pairing_url, "qr_type": "research_os_pairing", "session_in_qr": False})\n                return\n            if path == "/v1/auth/pairing/cancel":\n                self._send(HTTPStatus.OK, cancel_pairing(str(body.get("pairing_id") or "").strip(), str(body.get("pairing_secret") or "").strip()))\n                return\n'''
    if "/v1/auth/pairing/start" not in s:
        s = s.replace(post_marker, post_block + post_marker, 1)
    s = s.replace(
        "except (ValueError, KeyError, GoogleOAuthError, MultiLoginError, MultiLoginRuntimeError) as exc:",
        "except (ValueError, KeyError, GoogleOAuthError, MultiLoginError, MultiLoginRuntimeError, QRPairingError) as exc:",
    )
    path.write_text(s, encoding="utf-8", newline="\n")


def patch_client(path: Path):
    s = path.read_text(encoding="utf-8")
    if "startPairing()" not in s:
        marker = "  Future<Map<String, dynamic>> startProviderLogin(String provider) =>\n"
        block = '''  Future<Map<String, dynamic>> startPairing() =>\n      _postJson('/v1/auth/pairing/start', const <String, Object?>{});\n\n  Future<Map<String, dynamic>> getPairingStatus(\n    String pairingId,\n    String pairingSecret,\n  ) async {\n    final uri = _uri('/v1/auth/pairing/status').replace(\n      queryParameters: <String, String>{\n        'pairing_id': pairingId,\n        'secret': pairingSecret,\n      },\n    );\n    final response = await _client.get(uri);\n    return _decode(response);\n  }\n\n  Future<Map<String, dynamic>> cancelPairing(\n    String pairingId,\n    String pairingSecret,\n  ) =>\n      _postJson('/v1/auth/pairing/cancel', <String, Object?>{\n        'pairing_id': pairingId,\n        'pairing_secret': pairingSecret,\n      });\n\n'''
        if marker not in s:
            raise RuntimeError("API client insertion marker not found")
        s = s.replace(marker, block + marker, 1)
    path.write_text(s, encoding="utf-8", newline="\n")


def patch_pubspec(path: Path):
    s = path.read_text(encoding="utf-8")
    if "qr_flutter:" not in s:
        s = s.replace("  http: ^1.2.2\n", "  http: ^1.2.2\n  qr_flutter: ^4.1.0\n", 1)
    path.write_text(s, encoding="utf-8", newline="\n")


def local_validate(root: Path):
    app = root / "apps" / "research_os_flutter"
    run([sys.executable, "tools/research_os_api/test_qr_pairing.py"], root)
    run([sys.executable, "tools/research_os_api/test_server_auth_routes.py"], root)
    run([sys.executable, "-m", "py_compile", "tools/research_os_api/qr_pairing.py", "tools/research_os_api/server_auth_routes.py", "tools/research_os_api/server.py"], root)
    run(["flutter", "pub", "get"], app)
    run(["dart", "format", "--output=none", "--set-exit-if-changed", "lib/src/features/auth/login_page.dart", "lib/src/api/research_os_api_client.dart", "test/login_page_test.dart"], app)
    run(["flutter", "analyze", "lib/src/features/auth/login_page.dart", "lib/src/api/research_os_api_client.dart", "test/login_page_test.dart"], app)
    run(["flutter", "test", "test/login_page_test.dart"], app)
    run([sys.executable, "tools/research_os_m2_audit.py"], root)
    diff = run(["git", "diff", "--check"], root, check=False)
    if diff.returncode:
        raise RuntimeError("git diff --check failed")


def wait_pr_checks(root, pr):
    p = run(["gh", "pr", "checks", str(pr), "--watch", "--fail-fast"], root, check=False, capture=False)
    if p.returncode:
        raise RuntimeError("PR checks failed or did not complete successfully")


def wait_post_merge(root, main_sha):
    deadline = time.time() + 3600
    while time.time() < deadline:
        raw = out(["gh", "run", "list", "--repo", REPO, "--branch", "main", "--limit", "80", "--json", "databaseId,name,status,conclusion,headSha,event"], root)
        runs = json.loads(raw or "[]")
        selected = [r for r in runs if r.get("headSha") == main_sha and r.get("event") in {"push", "pull_request"}]
        if not selected:
            time.sleep(15)
            continue
        active = [r for r in selected if r.get("status") in {"queued", "in_progress", "waiting"}]
        failures = [r for r in selected if r.get("status") == "completed" and r.get("conclusion") not in {"success", "skipped", "neutral"}]
        for r in selected:
            print(f"POST-MERGE {r.get('databaseId')}: {r.get('name')} [{r.get('status')}/{r.get('conclusion')}]")
        if failures:
            raise RuntimeError("Post-merge workflow failure: " + "; ".join(f"{r.get('name')}={r.get('conclusion')}" for r in failures))
        if not active:
            return
        time.sleep(15)
    raise TimeoutError("Timed out waiting for post-merge workflows")


def ensure_clean_except_runner(root):
    status = out(["git", "status", "--short"], root)
    runner_path = Path(__file__).resolve()
    unrelated = []
    if status:
        for line in status.splitlines():
            path_text = line[3:].strip() if len(line) >= 4 else line.strip()
            path_text = path_text.strip('"')
            normalized = path_text.replace("/", "\\")
            if normalized == runner_path.name or normalized.endswith("\\" + runner_path.name):
                continue
            unrelated.append(line)
    if unrelated:
        raise RuntimeError(
            "Working tree has unrelated changes; resolve them before rollout:\n"
            + "\n".join(unrelated)
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    root = Path(parser.parse_args().repo).expanduser().resolve()
    for exe in ("git", "gh", "flutter", "dart"):
        if shutil.which(exe) is None:
            raise RuntimeError(f"Required executable not found: {exe}")
    ensure_clean_except_runner(root)
    remote = out(["git", "remote", "get-url", "origin"], root)
    if REPO not in remote:
        raise RuntimeError(f"Unexpected origin: {remote}")

    run(["git", "fetch", "origin"], root)
    run(["git", "switch", "main"], root)
    run(["git", "pull", "--ff-only", "origin", "main"], root)
    ensure_clean_except_runner(root)
    base = out(["git", "rev-parse", "HEAD"], root)
    print("Base main SHA:", base)

    if run(["git", "ls-remote", "--heads", "origin", BRANCH], root, check=False).stdout.strip():
        raise RuntimeError(f"Remote branch already exists: {BRANCH}")
    if out(["git", "branch", "--list", BRANCH], root):
        raise RuntimeError(f"Local branch already exists: {BRANCH}")

    run(["git", "switch", "-c", BRANCH, "origin/main"], root)
    write(root / "current" / "RESEARCH_OS_QR_PAIRING_CONTRACT.json", CONTRACT)
    write(root / "tools" / "research_os_api" / "qr_pairing.py", QR_MODULE)
    write(root / "tools" / "research_os_api" / "test_qr_pairing.py", TEST_QR)
    write(root / "tools" / "research_os_api" / "server_auth_routes.py", SERVER_AUTH)
    write(root / "apps" / "research_os_flutter" / "lib" / "src" / "features" / "auth" / "login_page.dart", LOGIN_PAGE)
    write(root / "apps" / "research_os_flutter" / "test" / "login_page_test.dart", LOGIN_TEST)
    patch_server(root / "tools" / "research_os_api" / "server.py")
    patch_client(root / "apps" / "research_os_flutter" / "lib" / "src" / "api" / "research_os_api_client.dart")
    patch_pubspec(root / "apps" / "research_os_flutter" / "pubspec.yaml")
    local_validate(root)

    run(["git", "add", "current/RESEARCH_OS_QR_PAIRING_CONTRACT.json", "tools/research_os_api/qr_pairing.py", "tools/research_os_api/test_qr_pairing.py", "tools/research_os_api/server_auth_routes.py", "tools/research_os_api/server.py", "apps/research_os_flutter/lib/src/features/auth/login_page.dart", "apps/research_os_flutter/lib/src/api/research_os_api_client.dart", "apps/research_os_flutter/test/login_page_test.dart", "apps/research_os_flutter/pubspec.yaml", "apps/research_os_flutter/pubspec.lock"], root)
    run(["git", "commit", "-m", COMMIT], root)
    feature_sha = out(["git", "rev-parse", "HEAD"], root)
    print("Feature SHA:", feature_sha)
    run(["git", "push", "-u", "origin", BRANCH], root)

    body = textwrap.dedent(f"""
    Replace the product login surface with one-time QR pairing.

    - QR is pairing only; it does not become identity, session, or permission authority.
    - Existing provider/runtime/session/handoff authorities remain canonical.
    - Owner role and authorization remain server-derived.
    - Shared Flutter surface becomes Scan to Connect.
    - Adds QR pairing contract, pairing store, API surface, tests, and M.2 audit coverage.

    Base: {base}
    Feature SHA: {feature_sha}
    """).strip()
    pr = run(["gh", "pr", "create", "--repo", REPO, "--base", "main", "--head", BRANCH, "--title", "feat: replace login surface with QR pairing", "--body", body], root).stdout.strip().splitlines()[-1]
    pr_number = pr.rstrip("/").split("/")[-1]
    print("PR:", pr)
    wait_pr_checks(root, pr_number)

    run(["gh", "pr", "merge", pr_number, "--repo", REPO, "--squash", "--delete-branch"], root)
    run(["git", "fetch", "origin", "main"], root)
    run(["git", "switch", "main"], root)
    run(["git", "reset", "--hard", "origin/main"], root)
    main_sha = out(["git", "rev-parse", "HEAD"], root)
    info = json.loads(out(["gh", "pr", "view", pr_number, "--repo", REPO, "--json", "state,merged,mergeCommit"], root))
    merge_sha = (info.get("mergeCommit") or {}).get("oid")
    if not info.get("merged") or (merge_sha and merge_sha != main_sha):
        raise RuntimeError(f"Main verification mismatch: PR={merge_sha}, main={main_sha}")
    print("Merged main SHA:", main_sha)
    run([sys.executable, "tools/research_os_api/test_qr_pairing.py"], root)
    run([sys.executable, "tools/research_os_m2_audit.py"], root)
    wait_post_merge(root, main_sha)
    print("FINAL: QR pairing rollout merged; exact main SHA verified; observed post-merge workflows complete")


if __name__ == "__main__":
    main()
