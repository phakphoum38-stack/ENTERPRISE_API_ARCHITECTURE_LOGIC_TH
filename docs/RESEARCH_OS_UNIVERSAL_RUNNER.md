# Research OS Universal Runner

Status: Active foundation

The existing `v3/research_os_v3/runner.py` remains the canonical stateless execution runner. This layer gives that Runner one platform-neutral contract for capabilities, CPU/RAM/NVMe resources, and platform-specific boot/runtime profiles.

## Lifecycle

```text
CREATED
  ↓
BOOTING
  ↓
DISCOVERING        optional
  ↓
INITIALIZING       optional
  ↓
PROVISIONING       optional
  ↓
READY
  ↓
EXECUTING
  ↓
RECOVERING         optional
  ↓
DRAINING
  ↓
DRAINED
  ↓
STOPPING
  ↓
STOPPED
```

A native host can use a short boot path such as `BOOT → DISCOVER → READY`; a toolchain runner may require initialization and provisioning. Profiles are descriptive and compatibility-bound; they do not grant authorization.

## Resource model

The Runner exposes a unified resource snapshot:

- CPU: architecture and logical CPU count; physical cores/frequency remain unknown unless a reliable adapter supplies them.
- RAM: total, available, used, and utilization where the host exposes the data.
- NVMe: the existing Memory Fabric T2 storage-backed tier; it is never represented as DRAM.
- Future families: GPU/VRAM, network, NUMA, CXL memory, remote memory, accelerators, and toolchains.

Unknown is preserved as unknown and is never promoted to available.

## Existing execution path

```text
Workflow Engine → Queue/Event → Stateless Runner → Execution → Result/Event
                                      │
                                      ├── Boot Profile
                                      ├── Capability Discovery
                                      ├── Resource Snapshot
                                      └── Execution Profile
```

This work does not create a second queue, scheduler, worker pool, execution engine, authorization authority, evidence authority, merge authority, or release authority.

## Isolation

Runner execution remains bound to the existing project/resource/authorization boundaries. The existing `REJECT_ON_CONFLICT` policy remains the resource conflict rule, and the Unified Final Gate remains the sole release authority.
