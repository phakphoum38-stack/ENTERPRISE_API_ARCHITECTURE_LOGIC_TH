from __future__ import annotations

import ctypes
import os
from collections.abc import Callable, Iterable
from ctypes import wintypes
from typing import Protocol


class SecretSource(Protocol):
    def get(self, name: str) -> str | None: ...


class EnvironmentSecretSource:
    """Read secrets from process environment without exposing them in contracts."""

    def get(self, name: str) -> str | None:
        value = os.environ.get(name)
        return value if value else None


class CompositeSecretSource:
    """Resolve a secret from the first configured source that contains it."""

    def __init__(self, sources: Iterable[SecretSource]) -> None:
        self._sources = tuple(sources)
        if not self._sources:
            raise ValueError("at least one secret source is required")

    def get(self, name: str) -> str | None:
        for source in self._sources:
            value = source.get(name)
            if value:
                return value
        return None


CredentialReader = Callable[[str], str | None]


class WindowsCredentialManagerSecretSource:
    """Read Generic Credentials from Windows Credential Manager.

    Credentials are addressed by target name only. The credential value is never
    included in provider status contracts or persisted by this source.
    """

    def __init__(
        self,
        *,
        target_prefix: str = "ResearchOSV3/",
        reader: CredentialReader | None = None,
    ) -> None:
        self.target_prefix = target_prefix
        self._reader = reader or _read_windows_generic_credential

    def get(self, name: str) -> str | None:
        return self._reader(f"{self.target_prefix}{name}")


def default_secret_source() -> SecretSource:
    """Prefer explicit process configuration, then the OS-native secret store."""

    return CompositeSecretSource(
        (
            EnvironmentSecretSource(),
            WindowsCredentialManagerSecretSource(),
        )
    )


def _read_windows_generic_credential(target: str) -> str | None:
    if os.name != "nt":
        return None

    credential_type_generic = 1
    error_not_found = 1168

    class CredentialW(ctypes.Structure):
        _fields_ = [
            ("Flags", wintypes.DWORD),
            ("Type", wintypes.DWORD),
            ("TargetName", wintypes.LPWSTR),
            ("Comment", wintypes.LPWSTR),
            ("LastWritten", wintypes.FILETIME),
            ("CredentialBlobSize", wintypes.DWORD),
            ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
            ("Persist", wintypes.DWORD),
            ("AttributeCount", wintypes.DWORD),
            ("Attributes", ctypes.c_void_p),
            ("TargetAlias", wintypes.LPWSTR),
            ("UserName", wintypes.LPWSTR),
        ]

    credential_pointer = ctypes.POINTER(CredentialW)
    advapi32 = ctypes.WinDLL("Advapi32.dll", use_last_error=True)
    cred_read = advapi32.CredReadW
    cred_read.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(credential_pointer),
    ]
    cred_read.restype = wintypes.BOOL
    cred_free = advapi32.CredFree
    cred_free.argtypes = [ctypes.c_void_p]
    cred_free.restype = None

    credential = credential_pointer()
    if not cred_read(target, credential_type_generic, 0, ctypes.byref(credential)):
        error = ctypes.get_last_error()
        if error == error_not_found:
            return None
        raise ctypes.WinError(error)

    try:
        size = int(credential.contents.CredentialBlobSize)
        if size <= 0:
            return None
        raw = ctypes.string_at(credential.contents.CredentialBlob, size)

        try:
            utf8 = raw.decode("utf-8").rstrip("\x00")
            if utf8 and "\x00" not in utf8:
                return utf8
        except UnicodeDecodeError:
            pass

        try:
            utf16 = raw.decode("utf-16-le").rstrip("\x00")
            return utf16 or None
        except UnicodeDecodeError as exc:
            raise RuntimeError("Windows credential contains unsupported text encoding") from exc
    finally:
        cred_free(credential)
