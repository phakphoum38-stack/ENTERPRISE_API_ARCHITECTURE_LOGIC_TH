# ANEF-006 — Design Principles

## Document Metadata

| Field | Value |
|---|---|
| Document ID | ANEF-006 |
| Document Name | Design Principles |
| Part | Part 1 — Foundation |
| Version | 1.0 Draft |
| Status | Draft |
| Classification | Public |
| Owner | ANEF Working Group |
| Depends On | ANEF-001 through ANEF-005 |
| Next Document | ANEF-007 — Glossary |

---

## 1. Purpose

เอกสารฉบับนี้แปลง Vision, Mission, Core Values และ Constitution ของ ANEF ให้เป็นหลักการออกแบบที่นำไปใช้ตัดสินใจเชิงสถาปัตยกรรมและวิศวกรรมได้จริง

Design Principles ไม่ใช่รายการเทคโนโลยีที่ต้องใช้ แต่เป็นเกณฑ์สำหรับเลือกโครงสร้าง ขอบเขต Contract ข้อมูล กระบวนการ และแนวทางการเปลี่ยนแปลงของระบบ

---

## 2. Scope

หลักการเหล่านี้ใช้กับ:

- Enterprise Architecture
- Application และ Platform Architecture
- AI Core และ Multi-Agent Systems
- API, Event และ Data Design
- Security, Privacy และ Identity
- Development, Testing, Delivery และ Operations
- Documentation และ Governance

แต่ละโครงการสามารถสร้าง Project-specific Principles เพิ่มเติมได้ แต่ต้องไม่ขัดกับ Constitution

---

## 3. Principle Format

แต่ละหลักการประกอบด้วย:

- **Statement** — ข้อความหลัก
- **Rationale** — เหตุผล
- **Implications** — ผลที่ต้องนำไปใช้
- **Evidence** — หลักฐานที่ใช้ตรวจสอบ
- **Trade-offs** — ข้อแลกเปลี่ยนที่ต้องยอมรับ

---

## 4. Core Design Principles

### DP-01 — Define Boundaries Before Components

**Statement:** ต้องกำหนดขอบเขตความรับผิดชอบ เจ้าของข้อมูล และ Trust Boundary ก่อนเลือก Component หรือเทคโนโลยี

**Rationale:** ระบบที่แบ่งขอบเขตไม่ชัดจะเกิด Coupling, Ownership Conflict และข้อมูลซ้ำ

**Implications:**

- ทุกโมดูลต้องมี Purpose และ Responsibility
- การสื่อสารข้ามขอบเขตต้องผ่าน Contract
- Shared Database หรือ Shared Mutable State ต้องมีเหตุผลรองรับ

**Evidence:** Context Map, Component Diagram, Ownership Matrix หรือ ADR

**Trade-offs:** ต้องใช้เวลาออกแบบก่อนเริ่ม Implementation

### DP-02 — One Capability, One Accountable Owner

**Statement:** ความสามารถสำคัญแต่ละด้านต้องมีเจ้าของหลักหนึ่งรายหรือหนึ่งทีมที่รับผิดชอบผลลัพธ์และวงจรชีวิต

**Rationale:** เจ้าของหลายรายโดยไม่มีผู้รับผิดชอบสุดท้ายทำให้การเปลี่ยนแปลงช้าและคุณภาพไม่แน่นอน

**Implications:**

- ระบุ Owner ของ Module, Data Product, API และ Policy
- Owner สามารถมอบหมายงานได้ แต่ความรับผิดชอบต้องไม่สูญหาย

**Evidence:** Ownership Registry, CODEOWNERS, Service Catalog

**Trade-offs:** ต้องจัดการกรณี Capability ที่ตัดข้ามหลายทีมอย่างชัดเจน

### DP-03 — Contracts Are First-Class Artifacts

**Statement:** Interface, API, Event, Schema และ Policy Contract ต้องถูกออกแบบ Version และทดสอบเป็น Artifact หลัก

**Rationale:** Contract ที่ชัดเจนช่วยให้โมดูลพัฒนาแยกกันและลดผลกระทบจากการเปลี่ยนแปลง

**Implications:**

- Contract ต้องมี Owner และ Compatibility Policy
- Breaking Change ต้องมี Migration Path
- Consumer Expectations ต้องถูกทดสอบเมื่อเหมาะสม

**Evidence:** API Specification, Event Schema, Contract Test

**Trade-offs:** เพิ่มภาระในการดูแล Version และ Compatibility

### DP-04 — Separate Policy from Mechanism

**Statement:** กฎทางธุรกิจ การอนุญาต และนโยบายการตัดสินใจควรแยกจากกลไกทางเทคนิคที่ใช้ดำเนินการ

**Rationale:** การแยกนี้ช่วยให้เปลี่ยน Policy โดยไม่ต้องรื้อ Infrastructure และเปลี่ยนเทคโนโลยีโดยไม่ทำลายกฎหลัก

**Implications:**

- Business Rule ไม่ควรถูกฝังใน UI หรือ Adapter
- Authorization Policy ควรแยกจาก Transport
- Vendor-specific Integration ควรอยู่หลัง Port หรือ Adapter

**Evidence:** Layer Diagram, Rule Catalog, Adapter Boundary

**Trade-offs:** อาจเพิ่มจำนวน Abstraction

### DP-05 — Prefer Explicit Data Flow

**Statement:** การไหลของข้อมูลและการเปลี่ยนสถานะต้องสามารถติดตามได้และหลีกเลี่ยง Side Effect ที่ซ่อนอยู่

**Rationale:** Data Flow ที่ชัดเจนช่วย Debug, Audit และ Test ได้ง่าย

**Implications:**

- ระบุ Input, Transformation, Output และ Owner
- Event และ Background Process ต้องมี Correlation
- หลีกเลี่ยง Global Mutable State

**Evidence:** Data Flow Diagram, Trace, Event Log

**Trade-offs:** ต้องเพิ่ม Metadata และ Observability

### DP-06 — Make State Ownership Explicit

**Statement:** State ทุกชนิดต้องมีเจ้าของ แหล่งจริง Lifecycle และ Consistency Model ที่ชัดเจน

**Rationale:** ความคลุมเครือด้าน State เป็นสาเหตุหลักของข้อมูลไม่ตรงกันและ Race Condition

**Implications:**

- ระบุ System of Record
- Cache, Replica และ Projection ต้องมีกฎ Sync
- Temporary State ต้องมี Expiration หรือ Cleanup

**Evidence:** Data Ownership Matrix, State Model, Retention Policy

**Trade-offs:** Consistency ที่เข้มงวดอาจแลกกับ Latency และ Availability

### DP-07 — Design for Failure

**Statement:** ระบบต้องสมมติว่า Dependency, Network, Storage, Human Input และ AI Output สามารถผิดพลาดได้

**Rationale:** Failure เป็นสภาวะปกติของระบบกระจายและระบบที่มีองค์ประกอบภายนอก

**Implications:**

- กำหนด Timeout, Retry, Idempotency และ Circuit Breaking ตามความเหมาะสม
- ต้องมี Degraded Mode หรือ Recovery Strategy สำหรับเส้นทางสำคัญ
- Retry ต้องไม่สร้างผลซ้ำที่เป็นอันตราย

**Evidence:** Failure Mode Analysis, Resilience Test, Runbook

**Trade-offs:** เพิ่มความซับซ้อนและต้นทุน Infrastructure

### DP-08 — Secure Defaults, Explicit Trust

**Statement:** ค่าเริ่มต้นต้องปลอดภัย และ Trust ทุกจุดต้องถูกประกาศ ไม่ใช่อนุมานจากตำแหน่งเครือข่ายหรือชื่อระบบ

**Rationale:** ความไว้วางใจโดยปริยายทำให้เกิดช่องโหว่และสิทธิ์เกินจำเป็น

**Implications:**

- Deny by Default
- Least Privilege
- Validate Input ที่ Boundary
- Secret ต้องไม่อยู่ใน Source Code หรือ Log

**Evidence:** Threat Model, Access Review, Security Test

**Trade-offs:** เพิ่มขั้นตอน Authentication, Authorization และ Key Management

### DP-09 — Privacy and Data Minimization

**Statement:** เก็บ ประมวลผล และส่งต่อเฉพาะข้อมูลที่จำเป็นตามวัตถุประสงค์ที่ประกาศไว้

**Rationale:** การลดข้อมูลช่วยลดผลกระทบด้าน Privacy, Security และ Compliance

**Implications:**

- ระบุ Purpose, Retention และ Access ของข้อมูลสำคัญ
- Mask หรือ Redact ข้อมูลใน Log และ Test Data
- ลบข้อมูลเมื่อหมดความจำเป็น

**Evidence:** Data Inventory, Retention Schedule, Privacy Review

**Trade-offs:** อาจลดความสะดวกในการวิเคราะห์ย้อนหลัง

### DP-10 — Observability Is Part of the Interface

**Statement:** Component ต้องเปิดเผยข้อมูลที่จำเป็นต่อการเข้าใจสุขภาพ ประสิทธิภาพ และความล้มเหลวของมัน

**Rationale:** ระบบที่ทำงานได้แต่สังเกตไม่ได้ไม่สามารถดูแลได้อย่างน่าเชื่อถือ

**Implications:**

- กำหนด Metric, Log, Trace และ Health Signal
- ใช้ Correlation ID ใน Flow สำคัญ
- Alert ต้องเชื่อมกับ Runbook และ Owner

**Evidence:** Dashboard, SLO, Alert Rule, Trace Sample

**Trade-offs:** มีต้นทุน Storage และการจัดการ Telemetry

### DP-11 — Test at the Cheapest Reliable Level

**Statement:** เลือกระดับการทดสอบที่ให้ความเชื่อมั่นเพียงพอด้วยต้นทุนต่ำที่สุด และเสริมด้วยการทดสอบระดับสูงเฉพาะจุดเสี่ยง

**Rationale:** การพึ่ง End-to-End Test มากเกินไปทำให้ช้าและเปราะ ขณะที่ Unit Test อย่างเดียวไม่ตรวจ Integration

**Implications:**

- ใช้ Unit Test สำหรับ Logic
- Contract Test สำหรับ Boundary
- Integration Test สำหรับ Dependency สำคัญ
- End-to-End Test สำหรับ Critical Journey

**Evidence:** Test Strategy, Coverage by Risk, Quality Gate

**Trade-offs:** ต้องออกแบบ Testability ตั้งแต่ต้น

### DP-12 — Automate Repeatable Rules

**Statement:** กฎที่ชัดเจน ทำซ้ำ และตรวจสอบได้ควรถูกทำให้เป็นอัตโนมัติ

**Rationale:** Automation ลดความผิดพลาดและทำให้มาตรฐานสม่ำเสมอ

**Implications:**

- ใช้ CI ตรวจ Format, Test, Security และ Documentation Link
- หลีกเลี่ยง Automation สำหรับ Judgment ที่ยังไม่มีกฎชัดเจน
- Automation ต้องมี Owner และ Failure Handling

**Evidence:** Pipeline, Policy-as-Code, Automated Report

**Trade-offs:** Automation เองต้องถูกดูแลและอาจสร้าง False Positive

### DP-13 — Keep Core Logic Portable

**Statement:** Core Domain และ Decision Logic ควรเป็นอิสระจาก UI, Transport, Storage และ Vendor SDK เท่าที่เหมาะสม

**Rationale:** Portability ช่วยให้เปลี่ยน Platform และทดสอบได้ง่าย

**Implications:**

- ใช้ Dependency Inversion
- Vendor SDK อยู่ใน Adapter Layer
- Core Logic ต้องรันใน Test Environment ได้โดยไม่พึ่งระบบภายนอก

**Evidence:** Dependency Diagram, Adapter Tests

**Trade-offs:** อาจต้องสร้าง Mapping และ Interface เพิ่ม

### DP-14 — Favor Evolutionary Architecture

**Statement:** ออกแบบให้เปลี่ยนแปลงเป็น Increment เล็ก ตรวจสอบได้ และย้อนกลับได้ แทนการรื้อครั้งใหญ่โดยไม่จำเป็น

**Rationale:** ระบบและความต้องการเปลี่ยนอย่างต่อเนื่อง การออกแบบที่ปรับตัวได้ลดความเสี่ยง

**Implications:**

- ใช้ Migration เป็นขั้นตอน
- รองรับ Parallel Run หรือ Feature Flag เมื่อเหมาะสม
- วัดผลก่อนและหลังการเปลี่ยนแปลง

**Evidence:** Migration Plan, Rollback Plan, Architecture Fitness Function

**Trade-offs:** ช่วงเปลี่ยนผ่านอาจต้องดูแลหลาย Version พร้อมกัน

### DP-15 — AI Output Is Untrusted Until Validated

**Statement:** ผลลัพธ์จาก AI ต้องถือว่าอาจผิด ไม่ครบ ล้าสมัย หรือไม่สอดคล้องกับ Policy จนกว่าจะผ่าน Validation

**Rationale:** AI มีความไม่แน่นอนและสามารถสร้างคำตอบที่ดูน่าเชื่อแต่ไม่ถูกต้อง

**Implications:**

- ใช้ Schema Validation, Test, Source Check หรือ Human Review ตามความเสี่ยง
- ห้ามให้ AI ดำเนินการผลกระทบสูงโดยไม่มี Guardrail และ Approval
- บันทึก Model/Configuration/Prompt Version เมื่อจำเป็นต่อ Audit

**Evidence:** Evaluation Result, Approval Record, Validation Log

**Trade-offs:** ลดความเร็วของ Automation บางประเภท

### DP-16 — Human Control Must Match Risk

**Statement:** ระดับการอนุมัติและการแทรกแซงของมนุษย์ต้องเพิ่มตามผลกระทบ ความไม่แน่นอน และความย้อนกลับไม่ได้ของการกระทำ

**Rationale:** งานความเสี่ยงต่ำสามารถอัตโนมัติได้มาก แต่งานผลกระทบสูงต้องมี Accountability ที่ชัดเจน

**Implications:**

- จัดประเภท Action ตาม Risk Tier
- กำหนด Auto-execute, Review-before-execute และ Prohibited Action
- Emergency Override ต้องถูก Audit

**Evidence:** Risk Matrix, Approval Policy, Audit Trail

**Trade-offs:** Human Review อาจเป็นคอขวดหากออกแบบไม่ดี

### DP-17 — Documentation Is an Executable Contract Where Possible

**Statement:** เอกสารควรเชื่อมกับเครื่องมือ Validation และ Source Artifacts เมื่อสามารถทำได้

**Rationale:** เอกสารที่ตรวจสอบอัตโนมัติได้มีโอกาสล้าหลังน้อยกว่า

**Implications:**

- Generate Reference จาก Source of Truth เมื่อเหมาะสม
- ตรวจ Broken Link, Schema และ Metadata ใน CI
- Example Code ควรถูก Test หรือ Compile ได้

**Evidence:** Documentation Pipeline, Link Check, Generated Spec

**Trade-offs:** ต้องลงทุนใน Tooling และรักษาความอ่านง่าย

### DP-18 — Measure Outcomes, Not Activity

**Statement:** การประเมินระบบและทีมต้องเน้นผลลัพธ์ คุณภาพ และความเสี่ยง ไม่ใช่ปริมาณ Commit, Ticket หรือเอกสารเพียงอย่างเดียว

**Rationale:** Activity สูงไม่ได้แปลว่าสร้างคุณค่าหรือความน่าเชื่อถือ

**Implications:**

- ใช้ KPI ที่เชื่อมกับ Reliability, Lead Time, Quality และ User Outcome
- หลีกเลี่ยง Metric ที่กระตุ้นพฤติกรรมผิด

**Evidence:** KPI Definition, Outcome Review, Trend Analysis

**Trade-offs:** Outcome บางชนิดวัดยากและมีปัจจัยภายนอก

---

## 5. Principle Prioritization

เมื่อหลักการขัดกัน ให้ใช้แนวทางดังนี้:

1. ปฏิบัติตาม Constitution ก่อน
2. ให้ Security, Privacy และ Safety มาก่อนความสะดวก
3. ให้ความถูกต้องของข้อมูลและ Accountability มาก่อนความเร็ว
4. เลือกแนวทางที่ลด Irreversible Risk
5. บันทึก Trade-off เป็น ADR

ไม่มีหลักการใดใช้แทนการวิเคราะห์บริบทได้

---

## 6. Architecture Decision Test

ก่อนอนุมัติการออกแบบ ให้ตอบคำถามต่อไปนี้:

- Boundary และ Owner ชัดเจนหรือไม่
- Source of Truth อยู่ที่ใด
- Contract และ Compatibility ถูกกำหนดหรือไม่
- Failure Mode และ Recovery คืออะไร
- Security, Privacy และ Trust Boundary ถูกวิเคราะห์หรือไม่
- State และ Data Lifecycle ชัดเจนหรือไม่
- ระบบสังเกตและตรวจสอบได้หรือไม่
- Test Strategy สอดคล้องกับ Risk หรือไม่
- Vendor Coupling ถูกจำกัดหรือมีเหตุผลหรือไม่
- การเปลี่ยนแปลงย้อนกลับหรือย้ายระบบได้หรือไม่
- AI Output และ Human Approval ถูกกำหนดตาม Risk หรือไม่
- เอกสารและหลักฐานใดรองรับการตัดสินใจ

---

## 7. Conformance

โครงการที่อ้างว่าสอดคล้องกับ ANEF Design Principles ต้อง:

- ใช้หลักการเหล่านี้ในการ Architecture Review
- บันทึก Trade-off ที่มีนัยสำคัญ
- ระบุข้อยกเว้นและผู้อนุมัติ
- มี Evidence ตามระดับความเสี่ยง
- ทบทวนหลักการเมื่อ Architecture หรือ Context เปลี่ยน

ไม่จำเป็นต้องใช้ Pattern เดียวกันทุกโครงการ แต่ต้องอธิบายได้ว่าการออกแบบสนับสนุนหลักการอย่างไร

---

## 8. Anti-Patterns

- เลือกเทคโนโลยีก่อนกำหนดปัญหาและ Boundary
- ใช้ Microservices โดยไม่มี Ownership และ Contract
- สร้าง Abstraction ทุกจุดโดยไม่มีความต้องการเปลี่ยนแปลงจริง
- เก็บ State หลายที่โดยไม่มี Consistency Model
- Retry ทุก Error โดยไม่วิเคราะห์ Idempotency
- เก็บ Log ทุกอย่างรวมถึงข้อมูลลับ
- วัดคุณภาพจาก Code Coverage เพียงค่าเดียว
- ใช้ AI เป็นผู้อนุมัติการเปลี่ยนแปลงของตัวเอง
- สร้างเอกสารที่ไม่เชื่อมกับ Source หรือไม่มี Owner
- อ้าง Vendor Neutrality แต่ Core Logic ใช้ Vendor SDK โดยตรง

---

## 9. Review Checklist

- [ ] ระบุ Principle ที่เกี่ยวข้องกับการตัดสินใจแล้ว
- [ ] ระบุ Boundary, Owner, Contract และ Source of Truth แล้ว
- [ ] วิเคราะห์ Failure, Security, Privacy และ Compatibility แล้ว
- [ ] มี Validation Strategy สำหรับ AI Output แล้ว
- [ ] มี Test, Observability และ Recovery Plan ที่เหมาะสมแล้ว
- [ ] Trade-off และข้อยกเว้นถูกบันทึกแล้ว
- [ ] เอกสารสอดคล้องกับ Implementation Plan แล้ว

---

## 10. Cross References

- ANEF-001 — Project Overview
- ANEF-002 — Vision
- ANEF-003 — Mission
- ANEF-004 — Core Values
- ANEF-005 — Constitution
- ANEF-007 — Glossary
- Future: Enterprise Architecture Principles
- Future: Security Architecture
- Future: AI Governance and Risk Model

---

## 11. Revision History

| Version | Date | Status | Description |
|---|---|---|---|
| 1.0 Draft | 2026-08-05 | Draft | Initial Design Principles |
