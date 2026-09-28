# Research OS Memory Fabric Architecture

## Status

ACTIVE foundation. This is a storage-backed memory-tier abstraction, not a replacement for DRAM.

## Purpose

Research OS can process datasets and checkpoints larger than available DRAM by using a tiered memory model. Python owns orchestration and policy-facing operations; the operating system and native storage stack remain responsible for hardware I/O.

## Architecture

Application / Workflow
        |
        v
Memory Fabric
        |
  +-----+-----+----------------+
  |           |                |
 DRAM       NVMe          Persistent
  T1         T2               T3
              |
          PCIe 5.0
       (capability, not
          requirement)

## Initial implementation

tools/research_os_api/memory_fabric.py provides a bounded mmap-backed region. If its backing path is placed on an M.2 NVMe PCIe 5.0 volume, the region uses that storage through the normal OS storage stack.

Python does not convert NVMe into DRAM. It exposes a controlled storage-backed region that can be used for large working sets.

## Long-term tiers

- T0 CPU cache
- T1 DRAM
- T2 NVMe
- T3 persistent storage
- Future adapters: GPU VRAM, NUMA-aware memory, CXL memory, remote memory

## Placement

- HOT -> DRAM
- WARM -> NVMe
- COLD -> NVMe or persistent storage
- PERSIST -> persistent storage

The first implementation does not implement automatic migration or prediction. Those are future capabilities and must be introduced behind the same abstraction.

## Isolation

Memory regions must remain scoped to project and owner/session boundaries. Cache or scratch data must never cross those boundaries. Evidence must retain project identity and provenance.

## Future roadmap

1. Hot/warm/cold promotion and demotion.
2. Pressure-aware eviction.
3. Prefetch based on observed access patterns.
4. Checkpoint-aware placement and recovery.
5. Compression where CPU cost is justified.
6. GPU/VRAM adapter.
7. NUMA awareness.
8. CXL memory adapter.
9. Remote-memory adapter.

## Boundaries

- No new queue, scheduler, authorization, evidence, or release authority.
- No claim that NVMe latency equals DRAM latency.
- No hard requirement for PCIe 5.0.
- Unknown hardware capability remains unknown.
