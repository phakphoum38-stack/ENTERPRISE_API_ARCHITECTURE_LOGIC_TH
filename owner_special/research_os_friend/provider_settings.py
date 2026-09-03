from __future__ import annotations

import ctypes
import json
import os
import urllib.error
import urllib.request
from ctypes import wintypes
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol
from urllib.parse import urlparse


class SecretStore(Protocol):
    backend: str
    def read(self) -> str | None: ...
    def write(self, value: str) -> None: ...


class MemorySecretStore:
    backend = "memory-test"
    def __init__(self) -> None: self._value: str | None = None
    def read(self) -> str | None: return self._value
    def write(self, value: str) -> None: self._value = value


class _DataBlob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]


class WindowsDpapiSecretStore:
    backend = "windows-dpapi-machine"
    CRYPTPROTECT_LOCAL_MACHINE = 0x4

    def __init__(self, path: Path) -> None:
        if os.name != "nt": raise RuntimeError("Windows DPAPI is available only on Windows")
        self.path = Path(path).resolve()
        self._crypt32 = ctypes.WinDLL("Crypt32.dll", use_last_error=True)
        self._kernel32 = ctypes.WinDLL("Kernel32.dll", use_last_error=True)
        self._kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        self._kernel32.LocalFree.restype = ctypes.c_void_p

    @staticmethod
    def _blob(data: bytes) -> tuple[_DataBlob, object]:
        buffer = ctypes.create_string_buffer(data)
        return _DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))), buffer

    def write(self, value: str) -> None:
        source, keepalive = self._blob(value.encode("utf-8")); protected = _DataBlob()
        ok = self._crypt32.CryptProtectData(ctypes.byref(source), "Research OS Owner Special", None, None, None, self.CRYPTPROTECT_LOCAL_MACHINE, ctypes.byref(protected))
        if not ok: raise ctypes.WinError(ctypes.get_last_error())
        try: encrypted = ctypes.string_at(protected.pbData, protected.cbData)
        finally: self._kernel32.LocalFree(protected.pbData); del keepalive
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp"); temporary.write_bytes(encrypted); os.replace(temporary, self.path)

    def read(self) -> str | None:
        if not self.path.is_file(): return None
        source, keepalive = self._blob(self.path.read_bytes()); plain = _DataBlob()
        ok = self._crypt32.CryptUnprotectData(ctypes.byref(source), None, None, None, None, 0, ctypes.byref(plain))
        if not ok: raise ctypes.WinError(ctypes.get_last_error())
        try: return ctypes.string_at(plain.pbData, plain.cbData).decode("utf-8")
        finally: self._kernel32.LocalFree(plain.pbData); del keepalive


@dataclass(frozen=True)
class ProviderConfig:
    enabled: bool = False
    base_url: str = ""
    model: str = ""


class ProviderSettingsStore:
    def __init__(self, path: Path) -> None: self.path = Path(path).resolve()
    def load(self) -> ProviderConfig:
        if not self.path.is_file(): return ProviderConfig()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return ProviderConfig(bool(payload.get("enabled", False)), str(payload.get("base_url", "")), str(payload.get("model", "")))
    def save(self, config: ProviderConfig) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(asdict(config), sort_keys=True, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, self.path)


class JsonTransport(Protocol):
    def get_json(self, url: str, *, headers: dict[str, str], timeout: float) -> dict[str, object]: ...
    def post_json(self, url: str, *, headers: dict[str, str], payload: dict[str, object], timeout: float) -> dict[str, object]: ...


class UrllibJsonTransport:
    @staticmethod
    def _open(request: urllib.request.Request, timeout: float) -> dict[str, object]:
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response: decoded = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace"); raise RuntimeError(f"provider HTTP {exc.code}: {body[:300]}") from exc
        if not isinstance(decoded, dict): raise RuntimeError("provider response must be a JSON object")
        return decoded
    def get_json(self, url: str, *, headers: dict[str, str], timeout: float) -> dict[str, object]:
        return self._open(urllib.request.Request(url, headers=headers, method="GET"), timeout)
    def post_json(self, url: str, *, headers: dict[str, str], payload: dict[str, object], timeout: float) -> dict[str, object]:
        body = json.dumps(payload).encode("utf-8")
        return self._open(urllib.request.Request(url, data=body, headers={**headers, "Content-Type": "application/json"}, method="POST"), timeout)


@dataclass
class OpenAICompatibleProvider:
    base_url: str
    model: str
    api_key: str
    transport: JsonTransport
    timeout: float = 20.0
    name: str = "openai-compatible"
    def _headers(self) -> dict[str, str]: return {"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"}
    def test_connection(self) -> dict[str, object]:
        payload = self.transport.get_json(f"{self.base_url.rstrip('/')}/models", headers=self._headers(), timeout=self.timeout)
        return {"connected": True, "provider": self.name, "models_visible": len(payload.get("data", []) or [])}
    def complete(self, *, prompt: str, context: tuple[str, ...]) -> str:
        messages: list[dict[str, str]] = []
        if context: messages.append({"role": "system", "content": "Owner context:\n" + "\n".join(context[-12:])})
        messages.append({"role": "user", "content": prompt})
        payload = self.transport.post_json(f"{self.base_url.rstrip('/')}/chat/completions", headers=self._headers(), payload={"model": self.model, "messages": messages}, timeout=self.timeout)
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices: raise RuntimeError("provider response has no choices")
        first = choices[0]
        if not isinstance(first, dict) or not isinstance(first.get("message"), dict): raise RuntimeError("provider response has no message")
        content = first["message"].get("content")
        if not isinstance(content, str) or not content.strip(): raise RuntimeError("provider response content is empty")
        return content


class ProviderManager:
    def __init__(self, data_root: Path, owner_id: str, *, secret_store: SecretStore | None = None, transport: JsonTransport | None = None) -> None:
        owner_root = Path(data_root).resolve() / "owners" / owner_id / "provider"
        self.settings = ProviderSettingsStore(owner_root / "settings.json")
        self.secret_store = secret_store or (WindowsDpapiSecretStore(owner_root / "provider-key.dpapi") if os.name == "nt" else MemorySecretStore())
        self.transport = transport or UrllibJsonTransport()
    @staticmethod
    def _validate(base_url: str, model: str) -> tuple[str, str]:
        normalized_url = base_url.strip().rstrip("/"); parsed = urlparse(normalized_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc: raise ValueError("base_url must be an http(s) URL")
        normalized_model = model.strip()
        if not normalized_model or len(normalized_model) > 200: raise ValueError("model is required")
        return normalized_url, normalized_model
    def configure(self, *, base_url: str, model: str, api_key: str | None = None, enabled: bool = True) -> dict[str, object]:
        normalized_url, normalized_model = self._validate(base_url, model)
        if api_key is not None and api_key.strip(): self.secret_store.write(api_key.strip())
        if enabled and not self.secret_store.read(): raise ValueError("api_key is required before enabling provider")
        self.settings.save(ProviderConfig(bool(enabled), normalized_url, normalized_model)); return self.safe_status()
    def provider(self) -> OpenAICompatibleProvider | None:
        config = self.settings.load(); key = self.secret_store.read()
        if not config.enabled or not key or not config.base_url or not config.model: return None
        return OpenAICompatibleProvider(config.base_url, config.model, key, self.transport)
    def launch_desk_config(self) -> tuple[str, str, str] | None:
        """Return provider credentials only to the in-process Launch Desk adapter."""
        config = self.settings.load(); key = self.secret_store.read()
        if not config.enabled or not key or not config.base_url or not config.model: return None
        return config.base_url, config.model, key
    def test(self) -> dict[str, object]:
        provider = self.provider()
        if provider is None: return {**self.safe_status(), "connected": False, "error": "provider_not_ready"}
        try: return {**self.safe_status(), **provider.test_connection()}
        except Exception as exc: return {**self.safe_status(), "connected": False, "error": type(exc).__name__}
    def safe_status(self) -> dict[str, object]:
        config = self.settings.load()
        return {"provider": "openai-compatible", "enabled": config.enabled, "base_url": config.base_url, "model": config.model, "credential_present": bool(self.secret_store.read()), "secret_backend": self.secret_store.backend, "secret_exposed": False}
