#!/usr/bin/env python3
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from credential_broker import CredentialBroker, CredentialBrokerError


class CredentialBrokerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.names = (
            "RESEARCH_OS_GEMINI_API_KEY",
            "GEMINI_API_KEY",
            "RESEARCH_OS_ANTHROPIC_API_KEY",
            "ANTHROPIC_API_KEY",
            "RESEARCH_OS_OPENAI_API_KEY",
            "OPENAI_API_KEY",
        )
        self.previous = {name: os.environ.get(name) for name in self.names}
        for name in self.names:
            os.environ.pop(name, None)

    def tearDown(self) -> None:
        for name, value in self.previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    def test_environment_compatibility_has_precedence(self) -> None:
        os.environ["GEMINI_API_KEY"] = "environment-secret"
        with tempfile.TemporaryDirectory() as tmp:
            broker = CredentialBroker(
                tmp,
                protect=lambda value: b"enc:" + value,
                unprotect=lambda value: value.removeprefix(b"enc:"),
            )
            broker.store("gemini", "stored-secret")
            self.assertEqual("environment-secret", broker.resolve("gemini"))
            self.assertEqual("environment", broker.status("gemini")["source"])

    def test_secure_store_round_trip_is_internal_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            broker = CredentialBroker(
                tmp,
                protect=lambda value: b"enc:" + value[::-1],
                unprotect=lambda value: value.removeprefix(b"enc:")[::-1],
            )
            broker.store("anthropic", "super-secret-value")
            self.assertEqual("super-secret-value", broker.resolve("anthropic"))
            status = broker.status("anthropic")
            self.assertTrue(status["present"])
            self.assertEqual("research-os-secure-store", status["source"])
            self.assertNotIn("super-secret-value", repr(status))
            raw = (Path(tmp) / "credentials" / "anthropic.bin").read_bytes()
            self.assertNotIn(b"super-secret-value", raw)

    def test_delete_removes_research_os_owned_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            broker = CredentialBroker(
                tmp,
                protect=lambda value: b"x" + value,
                unprotect=lambda value: value[1:],
            )
            broker.store("openai", "secret")
            self.assertTrue(broker.has("openai-compatible"))
            self.assertTrue(broker.delete("openai-compatible"))
            self.assertFalse(broker.has("openai-compatible"))
            self.assertFalse(broker.delete("openai-compatible"))

    def test_store_rejects_empty_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            broker = CredentialBroker(tmp, protect=lambda value: value, unprotect=lambda value: value)
            with self.assertRaises(CredentialBrokerError):
                broker.store("gemini", "   ")

    def test_status_never_returns_environment_secret(self) -> None:
        os.environ["OPENAI_API_KEY"] = "must-not-leak"
        broker = CredentialBroker("unused")
        status = broker.status("openai-compatible")
        self.assertTrue(status["present"])
        self.assertNotIn("must-not-leak", repr(status))


if __name__ == "__main__":
    unittest.main()
