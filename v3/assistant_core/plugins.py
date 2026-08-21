from __future__ import annotations

from threading import RLock
from typing import Callable

from .models import PluginManifest

PluginHandler = Callable[..., object]


class PluginRegistry:
    """Runtime registry for optional capabilities; core code never imports plugins directly."""

    def __init__(self) -> None:
        self._manifests: dict[str, PluginManifest] = {}
        self._handlers: dict[str, PluginHandler] = {}
        self._lock = RLock()

    def register(self, manifest: PluginManifest, handler: PluginHandler) -> None:
        if not manifest.name.strip() or not manifest.version.strip():
            raise ValueError("plugin name and version are required")
        with self._lock:
            if manifest.name in self._manifests:
                raise ValueError(f"plugin already registered: {manifest.name}")
            self._manifests[manifest.name] = manifest
            self._handlers[manifest.name] = handler

    def unregister(self, name: str) -> None:
        with self._lock:
            self._manifests.pop(name, None)
            self._handlers.pop(name, None)

    def list_enabled(self) -> tuple[PluginManifest, ...]:
        with self._lock:
            return tuple(m for m in self._manifests.values() if m.enabled)

    def invoke(self, name: str, *args: object, **kwargs: object) -> object:
        with self._lock:
            manifest = self._manifests.get(name)
            handler = self._handlers.get(name)
        if manifest is None or handler is None:
            raise KeyError(f"unknown plugin: {name}")
        if not manifest.enabled:
            raise PermissionError(f"plugin disabled: {name}")
        return handler(*args, **kwargs)
