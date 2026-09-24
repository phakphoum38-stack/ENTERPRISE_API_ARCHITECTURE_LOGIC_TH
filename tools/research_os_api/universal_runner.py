"""Universal Runner capability and lifecycle descriptors.

This module extends the existing stateless Runner architecture with a
provider/platform-neutral description of boot profiles, capabilities, and
host resources. It is not a scheduler, queue, authorization authority, or
second execution engine.
"""
from __future__ import annotations

import os
import platform
from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from .memory_fabric import detect_host_capabilities


class RunnerError(ValueError):
    """Invalid runner contract state."""


class RunnerLifecycle(str, Enum):
    CREATED = "CREATED"
    BOOTING = "BOOTING"
    DISCOVERING = "DISCOVERING"
    INITIALIZING = "INITIALIZING"
    PROVISIONING = "PROVISIONING"
    READY = "READY"
    EXECUTING = "EXECUTING"
    RECOVERING = "RECOVERING"
    DRAINING = "DRAINING"
    DRAINED = "DRAINED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class ResourceSnapshot:
    cpu_architecture: str | None
    logical_cpus: int | None
    physical_cores: int | None
    frequency_hz: int | None
    ram_total_bytes: int | None
    ram_available_bytes: int | None
    ram_used_bytes: int | None
    ram_utilization: float | None
    nvme_detected: bool | None

    @property
    def cpu_available(self) -> bool:
        return self.logical_cpus is not None and self.logical_cpus > 0

    @property
    def ram_available(self) -> bool:
        return self.ram_total_bytes is not None and self.ram_total_bytes > 0


@dataclass(frozen=True)
class BootProfile:
    profile_id: str
    platform: str
    required_capabilities: frozenset[str] = frozenset()
    phases: tuple[str, ...] = ("BOOT", "READY")

    def __post_init__(self) -> None:
        if not self.profile_id.strip():
            raise RunnerError("profile_id is required")
        if not self.platform.strip():
            raise RunnerError("platform is required")
        allowed = {"BOOT", "DISCOVER", "INITIALIZE", "PROVISION", "READY"}
        if not self.phases or any(phase not in allowed for phase in self.phases):
            raise RunnerError("invalid boot phase")
        if self.phases[-1] != "READY":
            raise RunnerError("boot profile must terminate in READY")


@dataclass(frozen=True)
class RunnerDescriptor:
    runner_id: str
    platform: str
    architecture: str
    capabilities: frozenset[str]
    boot_profile: BootProfile
    lifecycle: RunnerLifecycle = RunnerLifecycle.CREATED
    resources: ResourceSnapshot | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.runner_id.strip():
            raise RunnerError("runner_id is required")
        if not self.platform.strip():
            raise RunnerError("platform is required")
        if not self.architecture.strip():
            raise RunnerError("architecture is required")
        if not self.capabilities:
            raise RunnerError("at least one capability is required")
        if self.boot_profile.platform != self.platform:
            raise RunnerError("boot profile platform mismatch")

    def transition(self, target: RunnerLifecycle) -> "RunnerDescriptor":
        allowed = {
            RunnerLifecycle.CREATED: {RunnerLifecycle.BOOTING, RunnerLifecycle.FAILED},
            RunnerLifecycle.BOOTING: {RunnerLifecycle.DISCOVERING, RunnerLifecycle.INITIALIZING, RunnerLifecycle.PROVISIONING, RunnerLifecycle.READY, RunnerLifecycle.FAILED},
            RunnerLifecycle.DISCOVERING: {RunnerLifecycle.INITIALIZING, RunnerLifecycle.PROVISIONING, RunnerLifecycle.READY, RunnerLifecycle.FAILED},
            RunnerLifecycle.INITIALIZING: {RunnerLifecycle.PROVISIONING, RunnerLifecycle.READY, RunnerLifecycle.FAILED},
            RunnerLifecycle.PROVISIONING: {RunnerLifecycle.READY, RunnerLifecycle.FAILED},
            RunnerLifecycle.READY: {RunnerLifecycle.EXECUTING, RunnerLifecycle.DRAINING, RunnerLifecycle.STOPPING, RunnerLifecycle.FAILED},
            RunnerLifecycle.EXECUTING: {RunnerLifecycle.READY, RunnerLifecycle.RECOVERING, RunnerLifecycle.DRAINING, RunnerLifecycle.FAILED},
            RunnerLifecycle.RECOVERING: {RunnerLifecycle.READY, RunnerLifecycle.FAILED},
            RunnerLifecycle.DRAINING: {RunnerLifecycle.DRAINED, RunnerLifecycle.FAILED},
            RunnerLifecycle.DRAINED: {RunnerLifecycle.STOPPING, RunnerLifecycle.STOPPED},
            RunnerLifecycle.STOPPING: {RunnerLifecycle.STOPPED, RunnerLifecycle.FAILED},
            RunnerLifecycle.STOPPED: set(),
            RunnerLifecycle.FAILED: {RunnerLifecycle.RECOVERING, RunnerLifecycle.STOPPING},
        }
        if target not in allowed[self.lifecycle]:
            raise RunnerError(f"invalid runner transition: {self.lifecycle.value}->{target.value}")
        return RunnerDescriptor(self.runner_id, self.platform, self.architecture, self.capabilities, self.boot_profile, target, self.resources, self.metadata)


def detect_host_resources() -> ResourceSnapshot:
    """Return conservative host CPU/RAM/NVMe observations."""
    logical_cpus = os.cpu_count()
    architecture = platform.machine() or None
    ram_total = ram_available = ram_used = None
    ram_utilization = None

    if os.path.isfile("/proc/meminfo"):
        values: dict[str, int] = {}
        with open("/proc/meminfo", "r", encoding="utf-8") as handle:
            for line in handle:
                key, _, raw = line.partition(":")
                parts = raw.strip().split()
                if key in {"MemTotal", "MemAvailable"} and parts:
                    try:
                        values[key] = int(parts[0]) * 1024
                    except ValueError:
                        continue
        ram_total = values.get("MemTotal")
        ram_available = values.get("MemAvailable")
        if ram_total is not None and ram_available is not None:
            ram_used = max(0, ram_total - ram_available)
            ram_utilization = ram_used / ram_total if ram_total else None

    capabilities = detect_host_capabilities()
    return ResourceSnapshot(
        cpu_architecture=architecture,
        logical_cpus=logical_cpus if logical_cpus and logical_cpus > 0 else None,
        physical_cores=None,
        frequency_hz=None,
        ram_total_bytes=ram_total,
        ram_available_bytes=ram_available,
        ram_used_bytes=ram_used,
        ram_utilization=ram_utilization,
        nvme_detected=capabilities["nvme_detected"],
    )


def default_boot_profile(platform_name: str) -> BootProfile:
    return BootProfile("native-host", platform_name, frozenset(), ("BOOT", "DISCOVER", "READY"))


__all__ = ["BootProfile","ResourceSnapshot","RunnerDescriptor","RunnerError","RunnerLifecycle","default_boot_profile","detect_host_resources"]
