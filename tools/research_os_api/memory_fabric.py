"""Research OS tiered memory foundation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import mmap
import os
import platform
from typing import BinaryIO

class MemoryFabricError(RuntimeError):
    """Base error for memory-fabric operations."""

class CapacityExceeded(MemoryFabricError):
    """Raised when a bounded memory allocation cannot be satisfied."""

@dataclass(frozen=True)
class MemoryTier:
    tier_id: str
    name: str
    persistent: bool

TIERS = (
    MemoryTier("T0", "CPU_CACHE", False),
    MemoryTier("T1", "DRAM", False),
    MemoryTier("T2", "NVME", True),
    MemoryTier("T3", "PERSISTENT_STORAGE", True),
)

@dataclass(frozen=True)
class MemoryRegion:
    key: str
    tier_id: str
    size: int
    path: Path | None = None

class NvmeMemoryRegion:
    """Bounded mmap-backed region. The backing file may reside on NVMe."""

    def __init__(self, path: str | os.PathLike[str], size: int) -> None:
        if size <= 0:
            raise ValueError("size must be positive")
        self.path = Path(path)
        self.size = size
        self._file: BinaryIO | None = None
        self._map: mmap.mmap | None = None

    def __enter__(self) -> "NvmeMemoryRegion":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.path.open("w+b")
        self._file.truncate(self.size)
        self._map = mmap.mmap(self._file.fileno(), self.size)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._map is not None:
            self._map.flush()
            self._map.close()
            self._map = None
        if self._file is not None:
            self._file.close()
            self._file = None

    def _require_open(self) -> mmap.mmap:
        if self._map is None:
            raise MemoryFabricError("region is not open")
        return self._map

    def write(self, offset: int, data: bytes) -> None:
        if offset < 0 or offset + len(data) > self.size:
            raise ValueError("write exceeds region bounds")
        self._require_open()[offset : offset + len(data)] = data

    def read(self, offset: int, length: int) -> bytes:
        if offset < 0 or length < 0 or offset + length > self.size:
            raise ValueError("read exceeds region bounds")
        return bytes(self._require_open()[offset : offset + length])

def detect_host_capabilities() -> dict[str, str | bool]:
    """Return conservative host facts without guessing PCIe/NVMe details."""
    return {
        "os": platform.system(),
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "nvme_backend": True,
        "pcie5_detected": False,
        "cxl_detected": False,
    }
