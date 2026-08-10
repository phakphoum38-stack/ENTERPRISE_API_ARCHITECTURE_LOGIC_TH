from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class V3BridgeStatus:
    available: bool
    module: str
    exports: tuple[str, ...]
    reason: str = ""


class V3Bridge:
    """Read-only discovery bridge to the Research OS V3 owned core contracts."""

    REQUIRED_EXPORTS = (
        "BrainCore",
        "UnifiedMasterOrchestrator",
        "SoftwareFactory",
        "FactoryExecutionEngine",
        "ProviderRegistry",
        "OpenAICompatibleProvider",
        "UserContext",
        "UserDataLayout",
    )

    def __init__(self, repository_root: Path | None = None) -> None:
        self.repository_root = Path(repository_root or Path.cwd()).resolve()

    def probe(self) -> V3BridgeStatus:
        v3_root = self.repository_root / "v3"
        if not v3_root.is_dir():
            return V3BridgeStatus(False, "research_os_v3", (), "v3 root not found")

        inserted = False
        value = str(v3_root)
        if value not in sys.path:
            sys.path.insert(0, value)
            inserted = True
        try:
            module = importlib.import_module("research_os_v3")
            exports = tuple(name for name in self.REQUIRED_EXPORTS if hasattr(module, name))
            missing = tuple(name for name in self.REQUIRED_EXPORTS if name not in exports)
            if missing:
                return V3BridgeStatus(False, module.__name__, exports, "missing exports: " + ", ".join(missing))
            return V3BridgeStatus(True, module.__name__, exports)
        except Exception as exc:  # discovery must not break the Friend runtime
            return V3BridgeStatus(False, "research_os_v3", (), f"{type(exc).__name__}: {exc}")
        finally:
            if inserted:
                try:
                    sys.path.remove(value)
                except ValueError:
                    pass

    def snapshot(self) -> dict[str, object]:
        status = self.probe()
        return {
            "available": status.available,
            "module": status.module,
            "exports": list(status.exports),
            "reason": status.reason,
        }
