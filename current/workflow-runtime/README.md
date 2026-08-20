# Workflow Runtime Foundation

สถานะ: `active`
Version: `v3.2.0`

เอกสารชุดนี้กำหนด **Architecture Contract** สำหรับ Workflow Runtime ของ Research OS โดยไม่ผูกกับภาษา, queue provider, database หรือ cloud provider ใดโดยเฉพาะ

## เป้าหมาย

ย้าย execution workload จำนวนมากออกจากการผูกติดกับ GitHub Actions โดยให้ Architecture Source of Truth กำหนด boundary ระหว่าง:

```text
Intent → Plan → Workflow Engine → Queue → Stateless Runner → Result/Event
```

GitHub Actions ยังคงทำหน้าที่ CI/CD และ repository automation ตาม contract เดิม

## Components

- **Workflow Engine** — owns workflow state, dependency resolution, retry and cancellation semantics
- **Queue** — durable delivery boundary between orchestration and execution
- **Runner** — stateless execution worker
- **Event Bus** — publishes lifecycle events for observability and downstream reactions
- **Artifact Store** — stores execution outputs independently from runner lifecycle

## Design rules

1. Engine ต้องเป็น source of truth ของ workflow state
2. Runner ห้ามถือ durable workflow state ไว้ใน process memory เพียงอย่างเดียว
3. Job delivery ต้องรองรับ at-least-once semantics และ idempotent execution
4. Retry ต้องกำหนดโดย policy ไม่ใช่ hard-code ใน runner
5. ทุก state transition ต้องมี event ที่ตรวจสอบย้อนหลังได้
6. Artifact ต้องอยู่นอก lifecycle ของ runner
7. implementation ต้องรักษา contract นี้โดยไม่ผูก architecture กับ provider

## Documents

- `workflow-schema.yml` — workflow/job contract
- `state-machine.yml` — lifecycle และ transition rules
- `events.yml` — event envelope และ lifecycle events
- `retry-policy.yml` — retry/timeout/cancellation policy

## Release status

This contract set is **active for v3.2.0**. Implementations must remain compatible with these contracts, and any breaking change requires a new versioned contract.
