#!/usr/bin/env python3
"""Research OS-owned credential broker for AI providers.

The broker keeps secret handling behind the API/service boundary. Environment
variables remain supported for compatibility. On Windows, persisted credentials
use machine-scope DPAPI so the desktop app can submit a secret to the localhost
service and the service can later resolve it without exposing the value back to
Flutter. This module never includes secret values in status reports.
"""

from __future__ import annotations

import ctypes
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable


class CredentialBrokerError(RuntimeError):
    pass


@dataclass(frozen=True)
class CredentialStatus:
    provider: str
    present: bool
    source: str


_ENV_NAMES: dict[str, tuple[str, ...]] = {
    "gemini": ("RESEARCH_OS_GEMINI_API_KEY", "GEMINI_API_KEY"),
    "anthropic": ("RESEARCH_OS_ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY"),
    "openai-compatible": ("RESEARCH_OS_OPENAI_API_KEY", "OPENAI_API_KEY"),
}

_ALIASES = {"openai": "openai-compatible"}


def _canonical(provider: str) -> str:
    value = provider.strip().lower()
    return _ALIASES.get(value, value)


def _default_data_dir() -> Path:
    configured = os.getenv("RESEARCH_OS_DATA_DIR", "").strip()
    if configured:
        return Path(configured)
    if os.name == "nt":
        program_data = os.getenv("PROGRAMDATA", r"C:\ProgramData")
        return Path(program_data) / "ResearchOS"
    return Path.home() / "ResearchOSData"


class CredentialBroker:
    def __init__(
        self,
        data_dir: str | Path | None = None,
        *,
        protect: Callable[[bytes], bytes] | None = None,
        unprotect: Callable[[bytes], bytes] | None = None,
    ) -> None:
        self.data_dir = Path(data_dir) if data_dir is not None else _default_data_dir()
        if protect is None and unprotect is None and os.name == "nt":
            protect = _dpapi_protect_machine
            unprotect = _dpapi_unprotect
        self._protect = protect
        self._unprotect = unprotect

    def _path(self, provider: str) -> Path:
        canonical = _canonical(provider)
        if canonical not in _ENV_NAMES:
            raise CredentialBrokerError(f"unsupported credential provider: {canonical}")
        return self.data_dir / "credentials" / f"{canonical}.bin"

    def _env_value(self, provider: str) -> str | None:
        canonical = _canonical(provider)
        for name in _ENV_NAMES.get(canonical, ()):
            value = os.getenv(name)
            if value and value.strip():
                return value.strip()
        return None

    def resolve(self, provider: str) -> str | None:
        """Return a credential to trusted backend code only."""
        canonical = _canonical(provider)
        env_value = self._env_value(canonical)
        if env_value is not None:
            return env_value
        path = self._path(canonical)
        if not path.is_file() or self._unprotect is None:
            return None
        try:
            encrypted = path.read_bytes()
            clear = self._unprotect(encrypted)
            value = clear.decode("utf-8").strip()
            return value or None
        except (OSError, UnicodeError, ValueError) as exc:
            raise CredentialBrokerError(f"credential store read failed for {canonical}: {exc}") from exc

    def has(self, provider: str) -> bool:
        return self.resolve(provider) is not None

    def status(self, provider: str) -> dict[str, object]:
        canonical = _canonical(provider)
        if self._env_value(canonical) is not None:
            result = CredentialStatus(canonical, True, "environment")
        else:
            path = self._path(canonical)
            result = CredentialStatus(
                canonical,
                bool(path.is_file() and self._unprotect is not None),
                "research-os-secure-store" if path.is_file() and self._unprotect is not None else "not-configured",
            )
        return asdict(result)

    def store(self, provider: str, secret: str) -> None:
        """Persist a provider secret in the Research OS-owned secure store.

        Production Windows uses machine-scope DPAPI. Tests may inject protect /
        unprotect callables so CI never depends on Windows crypto APIs.
        """
        canonical = _canonical(provider)
        value = secret.strip()
        if not value:
            raise CredentialBrokerError("credential must not be empty")
        if self._protect is None:
            raise CredentialBrokerError("secure credential persistence is unavailable on this platform")
        path = self._path(canonical)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            encrypted = self._protect(value.encode("utf-8"))
            temp = path.with_suffix(path.suffix + ".tmp")
            temp.write_bytes(encrypted)
            try:
                os.chmod(temp, 0o600)
            except OSError:
                pass
            os.replace(temp, path)
        except OSError as exc:
            raise CredentialBrokerError(f"credential store write failed for {canonical}: {exc}") from exc

    def delete(self, provider: str) -> bool:
        path = self._path(provider)
        try:
            path.unlink()
            return True
        except FileNotFoundError:
            return False
        except OSError as exc:
            raise CredentialBrokerError(f"credential delete failed: {exc}") from exc


class _DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", ctypes.c_uint32), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]


def _blob(data: bytes) -> tuple[_DATA_BLOB, ctypes.Array[ctypes.c_char]]:
    buffer = ctypes.create_string_buffer(data)
    return _DATA_BLOB(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))), buffer


def _dpapi_protect_machine(data: bytes) -> bytes:
    if sys.platform != "win32":
        raise CredentialBrokerError("Windows DPAPI is unavailable")
    source, source_buffer = _blob(data)
    destination = _DATA_BLOB()
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    CRYPTPROTECT_UI_FORBIDDEN = 0x1
    CRYPTPROTECT_LOCAL_MACHINE = 0x4
    ok = crypt32.CryptProtectData(
        ctypes.byref(source),
        "Research OS AI credential",
        None,
        None,
        None,
        CRYPTPROTECT_UI_FORBIDDEN | CRYPTPROTECT_LOCAL_MACHINE,
        ctypes.byref(destination),
    )
    del source_buffer
    if not ok:
        raise CredentialBrokerError("Windows DPAPI protect failed")
    try:
        return ctypes.string_at(destination.pbData, destination.cbData)
    finally:
        kernel32.LocalFree(destination.pbData)


def _dpapi_unprotect(data: bytes) -> bytes:
    if sys.platform != "win32":
        raise CredentialBrokerError("Windows DPAPI is unavailable")
    source, source_buffer = _blob(data)
    destination = _DATA_BLOB()
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    CRYPTPROTECT_UI_FORBIDDEN = 0x1
    ok = crypt32.CryptUnprotectData(
        ctypes.byref(source),
        None,
        None,
        None,
        None,
        CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(destination),
    )
    del source_buffer
    if not ok:
        raise CredentialBrokerError("Windows DPAPI unprotect failed")
    try:
        return ctypes.string_at(destination.pbData, destination.cbData)
    finally:
        kernel32.LocalFree(destination.pbData)
