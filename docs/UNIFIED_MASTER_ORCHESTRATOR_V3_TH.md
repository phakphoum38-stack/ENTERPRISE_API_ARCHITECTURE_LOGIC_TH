# Research OS V3 Unified Master Orchestrator

สถานะ: Integration Version — ยังไม่ Merge เข้า `main` และยังไม่สร้าง Release

## เป้าหมาย

รวมระบบ AI หลักของ Research OS ให้ทำงานเป็นเวอร์ชันเดียว โดยไม่สร้าง owner ซ้ำ:

1. **Governed Brain Core** — Memory, Context, Skills, Tools, Decision/Risk, Evidence,
   Secret Redaction, Governed Task Runner, Learning และ System Introspection
2. **Adaptive Compound Brain** — โหมด `6^3 = 216` และเพดาน `6^6 = 46,656`
3. **Adaptive Hierarchical AI Software Factory** — โปรไฟล์ `1^3`, `3^3`, `6^3`, `6^6`
4. **AgentOrchestrator เดิม** — เป็น canonical dependency graph เพียงชุดเดียว
5. **Provider Gateway เดิม** — ใช้ provider/key ที่ตั้งค่าไว้ โดยไม่เปิดเผยค่า secret

## Single-owner composition

`UnifiedMasterOrchestrator` เป็นชั้น composition ไม่ใช่ระบบ orchestration ชุดใหม่

| หน้าที่ | Owner |
|---|---|
| Master composition | `UnifiedMasterOrchestrator` |
| Governed Brain | `v2_brain_runtime.BRAIN_RUNTIME` |
| 6^3 / 6^6 Compound Brain | `brain_skills.BRAIN` |
| Dependency graph / orchestration | `agent_server.ORCHESTRATOR` |
| Software Factory | `software_factory.AdaptiveControlPlane` |
| Provider selection | Provider / AI Gateway เดิม |

## Capacity

- `1^3 = 1`
- `3^3 = 27`
- `6^3 = 216`
- `6^6 = 46,656` logical capacity
- Runtime เปิดเฉพาะ node/worker ที่งานต้องใช้
- ค่าเริ่มต้นของ Compound Brain จำกัด active worker ตาม budget/readiness
- ไม่สร้าง worker 46,656 ตัวพร้อมกัน

## Safety invariants

- ไม่มี second DAG
- งาน write ยังผ่าน permission + approval gate
- Secret ไม่ถูกส่งกลับผ่าน introspection
- ไม่มี unrestricted shell จาก Master layer
- Learning ไม่แก้ source code เอง
- ไม่มี automatic merge, tag, GitHub Release หรือ production deployment

## Unified API

V3 คง API เดิมและเพิ่มมุมมองรวม:

- `GET /v2/master`
- `POST /v2/master/plan`
- `GET /v2/intelligence/*`
- `POST /v2/intelligence/plan`
- `GET /v2/brain/skills`
- `GET /v2/brain/capacity`
- `GET /v2/brain/providers`
- `POST /v2/brain/plans`
- `POST /v2/brain/search`

`/v2/master/plan` เป็น planning-only: ไม่ execute tool และไม่ bypass approval.

## Build policy

ยังใช้ Lean GitHub Actions เดิม:
- `ci-lite.yml`
- `candidate.yml`
- `release.yml`

ระหว่างเขียนโค้ดให้ตรวจแบบ local/preflight ก่อน และ **ไม่ Build Setup EXE ทุก commit**.
เมื่อ integration เสร็จจึงค่อยรัน Candidate แบบ build-once ตามคำสั่งผู้ใช้.
