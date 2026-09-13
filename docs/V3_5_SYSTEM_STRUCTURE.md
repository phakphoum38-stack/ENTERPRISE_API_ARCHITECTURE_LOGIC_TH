# V3.5 System Structure

**Document ID:** ANEF-V35-STRUCTURE-001  
**Version:** v3.5  
**Status:** Recovery Baseline  
**Source Branch:** `agent/v3.5-worker-pool-hardening`  
**Baseline Commit:** `6832d74d784cdaad700261e8d5b0357a3b984ed7`

## 1. Recovery Rule

เอกสารนี้ทำหน้าที่เป็น index ของระบบ V3.5 ที่พบใน repository history และใช้หลัก **reuse existing capability before creating new implementation**

ไม่ถือว่า component ใดเสร็จสมบูรณ์เพียงเพราะมีไฟล์อยู่ ต้องผ่าน validation และ Final Gate ก่อน release

## 2. Core Architecture

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

## 3. Runtime Architecture

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

Worker เป็น execution unit ที่ stateless และไม่เป็นเจ้าของ security authority

## 4. Existing V3.5 Workflow Assets

จาก baseline พบ workflow assets สำหรับ orchestration, recovery/repair, research OS gates และ V3/V3.5 validation อยู่ใน repository เช่น:

- `workflows/generate-orchestrator.yml`
- `workflows/generate-orchestrator-hardening.yml`
- `workflows/v3.4-dlq-replay-ci.yml`
- `workflows/v3.5-pr-integrity.yml`
- `workflows/research-os-final-gate.yml`
- `workflows/research-os-gate.yml`
- `workflows/research-os-completion-validation.yml`
- `workflows/research-os-performance-gate.yml`
- `workflows/research-os-unified-10x10-gate.yml`
- `workflows/v3-candidate.yml`
- `workflows/v3-clean-core.yml`
- `workflows/v3-factory-execution.yml`
- `workflows/v3-provider-hardening.yml`

รายการนี้เป็น inventory จาก baseline ไม่ใช่การรับรองผลของ workflow แต่ละตัว

## 5. Orchestrator Contract

`generate-orchestrator.yml` มีแนวคิด branch-isolated repair path และ registry validation โดยมี stages เช่น inventory, validate, issue-read, dispatch และ repair

การซ่อมแซมต้องเกิดบน branch แยกและต้องกลับเข้าสู่ PR/Final Gate ตาม repository rulebook

## 6. Final Gate Contract

Final Gate ต้องเป็นจุดรวมผลเพียงจุดเดียวใน release path และต้องไม่ copy/paste validation logic ที่มีอยู่แล้วโดยไม่จำเป็น

เมื่อ validation ถูกแยกเป็น reusable workflow ให้เชื่อมผ่าน `workflow_call` หรือกลไก artifact/result ที่ตรวจสอบได้ แทนการอ้างผลจาก workflow run อื่นแบบกำกวม

## 7. External Tool Boundary

Flutter อยู่ภายนอก core architecture:

```text
Architecture Source of Truth
          ↓
Contract / Version / Interface
          ↓
External Tool / Client
```

Flutter ไม่มีสิทธิ์เป็น authority ของ authorization, entitlement หรือ execution decision

## 8. Required Security Boundaries

ต้อง DENY สำหรับ:

- Activation Lock bypass
- Passcode bypass
- MDM circumvention
- Credential theft
- Exploit delivery
- Unauthorized device access
- Security-control evasion

## 9. Required Evidence

Security-sensitive decisions ต้องสามารถตรวจสอบย้อนหลังด้วย:

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

## 10. Next Validation Order

```text
Inventory
 ↓
Contract Validation
 ↓
Security Boundary Validation
 ↓
Worker / Orchestrator Validation
 ↓
API / E2E Validation
 ↓
Final Gate
 ↓
PR Review
 ↓
Merge
```

ห้ามข้ามขั้นเพื่อทำให้สถานะดูเหมือนเสร็จ
