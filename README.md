# ENTERPRISE API ARCHITECTURE LOGIC TH — Master Rulebook V3.5

## 1. Purpose

Repository นี้เป็น **Architecture Source of Truth** สำหรับ AI Native Enterprise Framework (ANEF), Research OS และตรรกะสถาปัตยกรรมระดับ Enterprise

ระบบต้องเป็น defensive research / service-eligibility platform และห้าม implement, facilitate หรือ automate:

- Activation Lock bypass
- Passcode bypass
- MDM circumvention
- Credential theft
- Exploit delivery
- Unauthorized device access
- Security-control evasion

กติกานี้เป็นข้อบังคับกลางของทุก implementation, workflow และ tooling

## 2. Canonical Security Architecture

```text
Identity
  ↓
Capability
  ↓
Policy
  ↓
Authorization
  ↓
Entitlement
  ↓
Execution
  ↓
Evidence
```

Execution อนุญาตได้ต่อเมื่อ security decisions ที่จำเป็นทั้งหมดผ่านเท่านั้น

```text
Authorization == ALLOWED
AND
Entitlement == ACTIVE
        ↓
     EXECUTE

Otherwise
        ↓
      DENY
```

Client ห้ามสร้างหรือ override ผลการตัดสินใจของ server

## 3. Platform Architecture

```text
USER
 ↓
WEB / CLIENT
 ↓
API GATEWAY
 ↓
DEVICE SERVICE
 ↓
DEVICE REGISTRY
 ↓
DEVICE INTELLIGENCE
 ↓
ELIGIBILITY ENGINE
 ↓
AUTHORIZATION
 ↓
ENTITLEMENT
 ↓
SERVICE WORKFLOW
 ↓
AUDIT / EVIDENCE
```

## 4. Evidence Contract

ทุก security-sensitive decision ต้องสร้าง immutable evidence อย่างน้อยประกอบด้วย:

- event_id
- actor
- device_id
- service_id
- action
- policy_id
- policy_version
- policy_decision
- authorization_result
- timestamp
- correlation_id
- result

Evidence ห้ามถูกแก้ไขหลังสร้าง

## 5. Workflow / Git Rule

การเปลี่ยนแปลงต้องเดินตาม:

```text
Branch
 ↓
Validation
 ↓
Final Gate
 ↓
PR Review
 ↓
Merge
 ↓
main
```

CI validation ต้อง read-only และห้าม:

- push ตรงเข้า main
- rewrite main
- bypass required validation
- manufacture successful results

ห้ามสร้าง implementation ซ้ำ หาก capability เดิมมีอยู่แล้ว

## 6. Final Gate

Final Gate เป็น release authority เดียวของระบบ

Required gates:

1. Architecture validation
2. Security boundary validation
3. Code generation validation
4. External-tool validation
5. API / contract validation
6. E2E validation
7. Release validation

ทุก required gate ต้องผ่านก่อน merge/release

## 7. Orchestrator + Stateless Worker

งานจำนวนมากให้ใช้ event-driven architecture:

```text
Event
 ↓
Queue
 ↓
Stateless Worker Pool
 ↓
Execution
 ↓
Evidence
 ↓
Final Gate
```

Orchestrator ทำหน้าที่วางแผน/ประสานงานและต้องอยู่ภายใต้ policy, authorization และ execution boundaries

Worker ต้อง stateless, reproducible และไม่ถือ security authority แทน policy/authorization services

## 8. Flutter Rule

`phakphoum38-stack/flutter` เป็น **External Tool / Client** เท่านั้น

Flutter ไม่ใช่ security authority และต้องไม่ manufacture หรือ override:

- Identity
- Policy
- Authorization
- Eligibility
- Entitlement
- Execution decision

การเชื่อมต่อระหว่าง repository ต้องอ้างอิง Contract, Version และ Interface ที่ชัดเจน

## 9. Versioning Rule

ทุก version ต้องรักษา snapshot และ revision history:

- `versions/` เก็บ version snapshots
- `current/` ชี้สถานะที่กำลังพัฒนา
- ทุกเอกสารต้องมี Document ID, Version, Status และ Revision History
- ห้ามลบหรือเขียนทับ version เก่าโดยไม่มี decision record

## 10. V3.5 Recovery Baseline

V3.5 recovery baseline ที่ค้นพบจาก repository history คือ branch:

`agent/v3.5-worker-pool-hardening`

baseline commit:

`6832d74d784cdaad700261e8d5b0357a3b984ed7`

baseline นี้มี workflow/orchestration และ worker-pool related assets อยู่แล้ว จึงต้อง **reuse ก่อนสร้างใหม่**

## 11. Change Policy

ก่อนเพิ่ม implementation:

```text
Inspect existing code
 ↓
Identify missing capability
 ↓
Reuse existing capability
 ↓
Modify only missing capability
 ↓
Run validation
 ↓
Final Gate
```

หลักสำคัญคือ **ไม่ duplicate, ไม่ bypass, ไม่แก้ main โดยตรง**

## 12. Repository Structure Reference

```text
.
├── README.md                         # Master Rulebook
├── CHANGELOG.md
├── VERSION_INDEX.md
├── current/
├── versions/
├── owner-commands/
└── workflows/
```

รายละเอียด V3.5 และรายการ component ที่กู้คืนได้ถูกสรุปไว้ใน:

`docs/V3_5_SYSTEM_STRUCTURE.md`

> Design Once. Build Everywhere. Scale Forever.
