# ANEF-005 — Constitution

## Document Metadata

| Field | Value |
|---|---|
| Document ID | ANEF-005 |
| Document Name | Constitution |
| Part | Part 1 — Foundation |
| Version | 1.0 Draft |
| Status | Draft |
| Classification | Public |
| Owner | ANEF Working Group |
| Depends On | ANEF-001, ANEF-002, ANEF-003, ANEF-004 |
| Next Document | ANEF-006 — Design Principles |

---

## 1. Purpose

เอกสารฉบับนี้กำหนดรัฐธรรมนูญสูงสุดของ AI Native Enterprise Framework (ANEF) เพื่อใช้เป็นกติกากลางสำหรับการออกแบบ การพัฒนา การทบทวน การเปลี่ยนแปลง และการกำกับดูแล Framework รวมถึงโครงการที่ประกาศว่าสอดคล้องกับ ANEF

Constitution มีลำดับความสำคัญสูงกว่าคู่มือ ตัวอย่าง เทมเพลต และรายละเอียดเชิงเทคนิคอื่นภายใน Framework หากเอกสารระดับล่างขัดแย้งกับ Constitution ให้ยึด Constitution เป็นหลักจนกว่าจะมีการแก้ไขอย่างเป็นทางการ

---

## 2. Scope

Constitution ใช้กับ:

- เอกสารทุกฉบับภายใน ANEF
- Reference Architecture และ Template ของ ANEF
- กระบวนการตัดสินใจเชิงสถาปัตยกรรม
- การทำงานร่วมกันระหว่างมนุษย์ AI และระบบอัตโนมัติ
- โครงการที่เลือกใช้ ANEF เป็นมาตรฐานหลัก
- การออกเวอร์ชัน การเปลี่ยนแปลง และการเลิกใช้ข้อกำหนด

Constitution ไม่กำหนด Business Logic เฉพาะของแต่ละโครงการ และไม่บังคับให้ใช้ภาษา Framework Cloud Database หรือผู้ให้บริการ AI รายใด

---

## 3. Normative Language

คำต่อไปนี้ใช้ในความหมายเชิงข้อกำหนด:

- **MUST / ต้อง** — เป็นข้อบังคับที่จำเป็นต่อความสอดคล้อง
- **MUST NOT / ต้องไม่** — เป็นข้อห้าม
- **SHOULD / ควร** — ควรปฏิบัติ เว้นแต่มีเหตุผลและหลักฐานรองรับการยกเว้น
- **SHOULD NOT / ไม่ควร** — ควรหลีกเลี่ยง เว้นแต่มีเหตุผลรองรับ
- **MAY / สามารถ** — เป็นทางเลือก

การยกเว้นข้อกำหนด MUST ต้องผ่านการตัดสินใจที่บันทึก ตรวจสอบ และอนุมัติตาม Governance ของโครงการ

---

## 4. Constitutional Articles

### Article 1 — Long-term First

ทุกการตัดสินใจต้องพิจารณาความสามารถในการดูแลรักษา การเปลี่ยนแปลง และผลกระทบระยะยาวก่อนประโยชน์ระยะสั้น

โครงการต้องไม่เพิ่มหนี้ทางเทคนิคโดยไม่มีเจ้าของ แผนลดหนี้ และเหตุผลที่ตรวจสอบได้

### Article 2 — Architecture Before Implementation

การเปลี่ยนแปลงที่มีผลต่อขอบเขต ความรับผิดชอบ Interface ข้อมูล ความปลอดภัย หรือการติดตั้ง ต้องมีการออกแบบก่อนลงมือพัฒนา

ระดับรายละเอียดของการออกแบบต้องเหมาะสมกับขนาดและความเสี่ยงของการเปลี่ยนแปลง

### Article 3 — One Source of Truth

ข้อมูล ข้อกำหนด และตรรกะสำคัญแต่ละเรื่องต้องมีเจ้าของและแหล่งอ้างอิงหลักที่ระบุชัดเจน

สำเนา Projection และ Cache ต้องสามารถย้อนกลับไปยังแหล่งจริง และต้องมีกฎการซิงก์หรือการหมดอายุ

### Article 4 — Documentation Never Lags Behind Code

เอกสารและโค้ดต้องพัฒนาไปพร้อมกัน

การเปลี่ยนแปลงไม่ถือว่าสมบูรณ์หากเอกสารที่เกี่ยวข้องยังไม่ถูกอัปเดต หรือไม่มีเหตุผลชัดเจนว่าไม่จำเป็นต้องอัปเดต

### Article 5 — Every Change Has Evidence

การเปลี่ยนแปลงสำคัญต้องมีหลักฐานอย่างน้อยหนึ่งประเภท เช่น:

- Architecture Decision Record
- Requirement หรือ Issue
- Test Result
- Risk Assessment
- Benchmark
- Incident Analysis
- Review Record

หลักฐานต้องเชื่อมโยงกลับไปยังการเปลี่ยนแปลงได้

### Article 6 — Modular by Design

ระบบต้องแบ่งความรับผิดชอบเป็นโมดูลที่มีขอบเขตชัดเจน

การสื่อสารระหว่างโมดูลต้องผ่าน Contract ที่ประกาศไว้ และต้องหลีกเลี่ยงการเข้าถึงรายละเอียดภายในของโมดูลอื่นโดยตรง

### Article 7 — Security and Privacy by Design

ความปลอดภัยและความเป็นส่วนตัวต้องเป็นส่วนหนึ่งของการออกแบบ ไม่ใช่งานที่เพิ่มภายหลัง

ระบบต้องใช้หลัก Least Privilege, Explicit Trust Boundaries, Secure Defaults และ Data Minimization ตามระดับความเสี่ยง

### Article 8 — Quality Is Continuous

คุณภาพต้องถูกตรวจสอบตลอดวงจรการพัฒนา ไม่ใช่เฉพาะก่อน Release

ทุก Increment ต้องมี Quality Gate ที่เหมาะสม ครอบคลุมอย่างน้อยความถูกต้อง ความปลอดภัย ความเข้ากันได้ และผลกระทบต่อเอกสาร

### Article 9 — AI Is a Team Member, Human Governance Remains

AI สามารถช่วยวิเคราะห์ วางแผน เขียน ทดสอบ และตรวจสอบได้ แต่การตัดสินใจที่มีผลกระทบสูงต้องมีผู้รับผิดชอบที่เป็นมนุษย์หรือกลไก Governance ที่องค์กรอนุมัติ

ผลลัพธ์จาก AI ต้องถูกปฏิบัติเป็นข้อเสนอหรือ Artifact ที่ต้องผ่าน Validation ตามระดับความเสี่ยง

### Article 10 — Vendor and Technology Neutrality

ข้อกำหนดแกนกลางของ ANEF ต้องไม่ผูกกับผู้ให้บริการ ผลิตภัณฑ์ ภาษา หรือ Platform ใดโดยไม่จำเป็น

รายละเอียดเฉพาะเทคโนโลยีต้องอยู่ใน Adapter, Profile, Implementation Guide หรือ Decision Record ของโครงการ

### Article 11 — Explicit Ownership and Accountability

ทุกระบบ โมดูล ข้อมูล Contract และเอกสารสำคัญต้องมีเจ้าของที่ระบุได้

เจ้าของต้องรับผิดชอบต่อความถูกต้อง การเปลี่ยนแปลง ความเสี่ยง และวงจรชีวิตของสิ่งที่ตนดูแล

### Article 12 — Reversible Change Where Practical

การเปลี่ยนแปลงควรถูกออกแบบให้ Rollback, Migrate หรือ Disable ได้เมื่อเหมาะสม

การเปลี่ยนแปลงที่ย้อนกลับไม่ได้ต้องมีการประเมินผลกระทบ แผนสำรอง และการอนุมัติก่อนดำเนินการ

### Article 13 — Compatibility Is Managed Explicitly

ความเข้ากันได้ย้อนหลังต้องได้รับการจัดการอย่างมีแผน ไม่ใช่สมมติว่าเกิดขึ้นเอง

Breaking Change ต้องประกาศ ชี้ผลกระทบ จัดทำ Migration Path และใช้ Versioning ที่เหมาะสม

### Article 14 — Observability and Auditability

ระบบต้องสามารถอธิบายสถานะ การทำงานผิดพลาด และการตัดสินใจสำคัญผ่าน Log, Metric, Trace, Event หรือ Audit Record ตามความเหมาะสม

ข้อมูลสังเกตการณ์ต้องไม่ละเมิดข้อกำหนดด้านความเป็นส่วนตัวและความปลอดภัย

### Article 15 — Continuous Evolution Under Control

ANEF และระบบที่ใช้ ANEF ต้องสามารถพัฒนาอย่างต่อเนื่องผ่านกระบวนการเปลี่ยนแปลงที่มีเวอร์ชัน หลักฐาน การทบทวน และผลกระทบที่ตรวจสอบได้

การพัฒนาอย่างต่อเนื่องต้องไม่ทำลายหลักการแกนกลางโดยไม่มีการแก้ Constitution อย่างเป็นทางการ

---

## 5. Hierarchy of Authority

เมื่อเอกสารขัดแย้งกัน ให้ใช้ลำดับต่อไปนี้:

1. Constitution
2. Approved Governance Policies
3. Approved Architecture Decisions
4. Normative Specifications
5. Standards and Profiles
6. Guidelines
7. Templates and Examples

เอกสารระดับล่างต้องไม่เปลี่ยนความหมายของเอกสารระดับสูงกว่า

---

## 6. Decision and Exception Rules

ข้อยกเว้นต้องมี:

1. ข้อกำหนดที่ขอยกเว้น
2. เหตุผล
3. ขอบเขตและระยะเวลา
4. ผลกระทบและความเสี่ยง
5. มาตรการชดเชย
6. เจ้าของ
7. ผู้อนุมัติ
8. วันที่ทบทวนหรือวันหมดอายุ

ข้อยกเว้นถาวรต่อ Constitution ต้องดำเนินการเป็นการแก้รัฐธรรมนูญ ไม่ใช่บันทึกข้อยกเว้นทั่วไป

---

## 7. Amendment Process

การแก้ Constitution ต้อง:

- มีข้อเสนอเป็นลายลักษณ์อักษร
- อธิบายปัญหาและเหตุผล
- วิเคราะห์ผลกระทบต่อเอกสารและโครงการเดิม
- ระบุ Compatibility และ Migration Plan
- ผ่านการทบทวนโดยผู้มีส่วนได้ส่วนเสีย
- ได้รับการอนุมัติตาม Governance
- เพิ่ม Revision History และ Version ใหม่

การแก้ไขที่เปลี่ยนความหมายหลักควรเพิ่ม Major Version ของ ANEF

---

## 8. Conformance Requirements

โครงการที่ประกาศว่า **ANEF Conformant** ต้อง:

- ระบุ ANEF Version ที่ใช้
- ระบุ Profile และข้อยกเว้น
- มีเจ้าของ Architecture และ Documentation
- มีหลักฐานการตัดสินใจสำคัญ
- มี Quality Gate และ Security Review ตามความเสี่ยง
- สามารถแสดง Traceability จาก Requirement ไปยัง Implementation และ Validation ได้ในระดับที่เหมาะสม

การใช้เพียงชื่อโฟลเดอร์หรือ Template ของ ANEF ไม่ถือว่าเป็นความสอดคล้อง

---

## 9. Enforcement

การบังคับใช้ Constitution สามารถทำผ่าน:

- Human Review
- Architecture Review Board
- Pull Request Checklist
- Automated Policy Check
- CI Quality Gate
- Documentation Validation
- Release Approval
- Periodic Audit

กลไกบังคับใช้ควรเป็นอัตโนมัติเมื่อกฎสามารถตรวจสอบได้อย่างแน่นอน และใช้ Human Judgment เมื่อจำเป็นต้องพิจารณาบริบท

---

## 10. Anti-Patterns

- เขียนโค้ดก่อนแล้วค่อยสร้างเหตุผลย้อนหลัง
- มีแหล่งข้อมูลจริงหลายชุดโดยไม่มีเจ้าของ
- ใช้ AI ผลิตการเปลี่ยนแปลงแล้ว Merge โดยไม่ตรวจสอบ
- ผูก Core Architecture กับ Vendor โดยไม่มี Abstraction หรือ Decision Record
- ยอมรับ Breaking Change โดยไม่มี Migration Plan
- ใช้ข้อยกเว้นถาวรเพื่อหลีกเลี่ยงการแก้กฎ
- ปล่อยเอกสารล้าหลังโค้ด
- ไม่มีผู้รับผิดชอบต่อข้อมูลหรือโมดูลสำคัญ

---

## 11. Review Checklist

- [ ] การเปลี่ยนแปลงสอดคล้องกับ Articles ทั้งหมดหรือไม่
- [ ] มี One Source of Truth ที่ชัดเจนหรือไม่
- [ ] มีเจ้าของและหลักฐานหรือไม่
- [ ] เอกสารและ Test ได้รับการอัปเดตหรือไม่
- [ ] Security, Privacy และ Compatibility ได้รับการพิจารณาหรือไม่
- [ ] AI-generated artifacts ผ่าน Validation หรือไม่
- [ ] ข้อยกเว้นมีวันทบทวนและผู้อนุมัติหรือไม่

---

## 12. Cross References

- ANEF-001 — Project Overview
- ANEF-002 — Vision
- ANEF-003 — Mission
- ANEF-004 — Core Values
- ANEF-006 — Design Principles
- Future: Architecture Decision Record Standard
- Future: Change Management
- Future: Conformance Model

---

## 13. Revision History

| Version | Date | Status | Description |
|---|---|---|---|
| 1.0 Draft | 2026-08-05 | Draft | Initial Constitution |
