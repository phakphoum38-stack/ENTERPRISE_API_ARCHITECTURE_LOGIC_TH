# Research OS V3 Unified Master Orchestrator

สถานะ: Integration Version — ยังไม่ Merge เข้า `main` และยังไม่สร้าง Release

## เป้าหมาย

รวมระบบ AI หลักของ Research OS ให้ทำงานเป็นเวอร์ชันเดียว โดยไม่สร้าง owner ซ้ำ:

1. **Governed Brain Core** — Memory, Context, Skills, Tools, Decision/Risk, Evidence,
   Secret Redaction, Governed Task Runner, Learning และ System Introspection
2. **Adaptive Compound Brain** — โหมด `6^3 = 216` และเพดาน `6^6 = 46,656`
3. **Tool Intelligence** — เลือกเครื่องมือเดิมก่อน, หา capability gap, ค้น candidate เมื่อผู้ใช้ขอ, ประเมิน evidence และออกแบบ adapter plan โดยไม่ auto-install/execute
4. **Adaptive Hierarchical AI Software Factory** — โปรไฟล์ `1^3`, `3^3`, `6^3`, `6^6`
5. **AgentOrchestrator เดิม** — เป็น canonical dependency graph เพียงชุดเดียว
6. **Provider Gateway เดิม** — ใช้ provider/key ที่ตั้งค่าไว้ โดยไม่เปิดเผยค่า secret

## Single-owner composition

`UnifiedMasterOrchestrator` เป็นชั้น composition ไม่ใช่ระบบ orchestration ชุดใหม่

| หน้าที่ | Owner |
|---|---|
| Master composition | `UnifiedMasterOrchestrator` |
| Governed Brain | `v2_brain_runtime.BRAIN_RUNTIME` |
| 6^3 / 6^6 Compound Brain | `brain_skills.BRAIN` |
| Tool Registry | `BrainRuntime.tools` |
| Tool Intelligence | `v2_tool_intelligence.ToolIntelligence` |
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

## Tool Intelligence invariants

- เลือก registered/ready tool ที่ครอบคลุม capability ก่อน
- capability ที่ขาดถูกแสดงเป็น gap ก่อนค้น external tool
- external discovery เกิดเมื่อ objective ระบุให้ค้นหา tool/software/plugin/MCP
- candidate ต้องมี provenance/evidence ก่อนเสนอ
- adapter เป็น plan-only จนกว่าจะผ่าน review
- ไม่ auto-download
- ไม่ auto-install
- ไม่ auto-register
- ไม่ auto-grant permission
- ไม่ auto-execute external tool

## Service exposure authentication

Research OS ยังคง local-first:

- ค่าเริ่มต้นของ packaged Windows Service คือ `127.0.0.1`
- loopback ใช้งานได้โดยไม่ต้องฝัง shared application secret ใน Flutter app
- หาก HTTP server bind ออกนอก loopback จะ fail closed และต้องมี short-lived signed identity assertion
- ใช้ `developer_identity.IdentityAssertionVerifier` เดิม ไม่สร้าง auth verifier ซ้ำ
- assertion ใช้ principal + timestamp + nonce + HMAC signature
- nonce replay ถูกปฏิเสธ
- Flutter API client รองรับ request-header provider เพื่อรับ signed headers ใหม่ต่อ request โดยไม่ถือ signing secret เอง
- auth boundary ตัดสินจาก bind address จริงของ HTTP server ไม่เชื่อ environment string เพียงอย่างเดียว

## Safety invariants

- ไม่มี second DAG
- งาน write ยังผ่าน permission + approval gate
- Secret ไม่ถูกส่งกลับผ่าน introspection
- ไม่มี unrestricted shell จาก Master layer
- Learning ไม่แก้ source code เอง
- ไม่มี automatic merge, tag, GitHub Release หรือ production deployment

## Unified API

V3 คง API เดิมและเพิ่มมุมมองรวม โดย `tools/research_os_api/openapi.yaml` เป็น OpenAPI source หลัก:

- `GET /v2/providers`
- `GET /v2/master`
- `POST /v2/master/plan`
- `GET /v2/intelligence`
- `GET /v2/intelligence/capabilities`
- `GET /v2/intelligence/agents`
- `GET /v2/intelligence/skills`
- `GET /v2/intelligence/tools`
- `GET /v2/intelligence/permissions`
- `GET /v2/intelligence/architecture`
- `GET /v2/intelligence/project-state`
- `GET /v2/intelligence/health`
- `POST /v2/intelligence/plan`
- `GET /v2/brain/skills`
- `GET /v2/brain/capacity`
- `GET /v2/brain/providers`
- `POST /v2/brain/plans`
- `POST /v2/brain/search`

`/v2/master/plan` เป็น planning-only: ไม่ execute tool และไม่ bypass approval.

## Regression coverage ที่เพิ่มใน integration

- OpenAPI ต้องประกาศ Unified Master/Intelligence routes ใน source เดียว
- explicit `6^6` ต้อง route ไป `compound_6x6`
- Tool Intelligence external discovery ต้องยังเป็น evidence-backed/review-only
- loopback primary API ต้องยังทำงานโดยไม่ต้องใช้ signed identity header
- non-loopback primary API ต้องปฏิเสธ request ที่ไม่มี signed identity
- signed identity nonce เดิมต้องใช้ซ้ำไม่ได้
- Flutter API client ต้องขอ identity headers ใหม่ต่อ request เมื่อเปิด auth provider

## Build policy

ยังใช้ Lean GitHub Actions เดิม:
- `ci-lite.yml`
- `candidate.yml`
- `release.yml`

ระหว่างเขียนโค้ดให้ตรวจแบบ local/preflight ก่อน และ **ไม่ Build Setup EXE ทุก commit**.
เมื่อ integration เสร็จจึงค่อยรัน Candidate แบบ build-once ตามคำสั่งผู้ใช้.
