# Simulated Research OS Workspace

Purpose: isolated compatibility rehearsal for PR #41 → PR #47.

This is a structure-only simulation. It does not alter `main`, PR #47, V1 data, or production services.

```text
Virtual Root
├── Research OS
│   ├── Flutter GUI
│   ├── Main API :8787
│   ├── Owner/Friend + V3 :8790
│   └── Unified Master
├── Connectors
│   ├── ChatGPT/OpenAI
│   └── Google Drive
├── Legacy
│   └── V3 :8788 (preserved; no global migration)
└── Evidence
    ├── Build
    ├── Installer
    ├── V1 preservation
    └── SHA256
```

Simulation gates:

1. Verify topology.
2. Verify endpoint ownership.
3. Verify Unified Master authority.
4. Verify bounded execution/backpressure.
5. Verify preservation boundary.
6. Verify evidence flow.

No production merge is implied by this workspace.
