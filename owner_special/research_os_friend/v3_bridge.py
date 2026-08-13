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
    """Discovery and planning bridge to the Research OS V3 owned core."""

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

    def _v3_root(self) -> Path:
        return self.repository_root / "v3"

    def _insert_path(self) -> tuple[str, bool]:
        value = str(self._v3_root())
        inserted = False
        if value not in sys.path:
            sys.path.insert(0, value)
            inserted = True
        return value, inserted

    @staticmethod
    def _remove_path(value: str, inserted: bool) -> None:
        if inserted:
            try:
                sys.path.remove(value)
            except ValueError:
                pass

    def probe(self) -> V3BridgeStatus:
        if not self._v3_root().is_dir():
            return V3BridgeStatus(False, "research_os_v3", (), "v3 root not found")

        value, inserted = self._insert_path()
        try:
            module = importlib.import_module("research_os_v3")
            exports = tuple(name for name in self.REQUIRED_EXPORTS if hasattr(module, name))
            missing = tuple(name for name in self.REQUIRED_EXPORTS if name not in exports)
            if missing:
                return V3BridgeStatus(False, module.__name__, exports, "missing exports: " + ", ".join(missing))
            return V3BridgeStatus(True, module.__name__, exports)
        except Exception as exc:
            return V3BridgeStatus(False, "research_os_v3", (), f"{type(exc).__name__}: {exc}")
        finally:
            self._remove_path(value, inserted)

    def factory_plan(self, scale: str) -> dict[str, object]:
        """Return the certified V3 SoftwareFactory stage plan for a Friend scale."""
        status = self.probe()
        if not status.available:
            return {"available": False, "scale": scale, "stages": [], "reason": status.reason}

        value, inserted = self._insert_path()
        try:
            factory_module = importlib.import_module("research_os_v3.factory")
            models_module = importlib.import_module("research_os_v3.models")
            profile = next(
                item for item in models_module.SCALE_PROFILES
                if item.tier.value == scale
            )
            plan = factory_module.SoftwareFactory().plan(profile)
            return {
                "available": True,
                "scale": plan.profile.tier.value,
                "capacity": plan.maximum_leaf_capacity,
                "stages": [stage.name for stage in plan.stages],
            }
        except Exception as exc:
            return {"available": False, "scale": scale, "stages": [], "reason": f"{type(exc).__name__}: {exc}"}
        finally:
            self._remove_path(value, inserted)

    def snapshot(self) -> dict[str, object]:
        status = self.probe()
        return {
            "available": status.available,
            "module": status.module,
            "exports": list(status.exports),
            "reason": status.reason,
        }
