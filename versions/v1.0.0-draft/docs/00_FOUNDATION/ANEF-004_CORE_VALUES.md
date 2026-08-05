# ANEF-004 — Core Values

## Document Metadata

| Field | Value |
|---|---|
| Document ID | ANEF-004 |
| Document Name | Core Values |
| Part | Part 1 — Foundation |
| Version | 1.0 Draft |
| Status | Draft |
| Classification | Public |
| Owner | ANEF Working Group |
| Depends On | ANEF-001, ANEF-002, ANEF-003 |
| Next Document | ANEF-005 — Constitution |

---

## 1. Purpose

เอกสารฉบับนี้กำหนดค่านิยมหลักของ **AI Native Enterprise Framework (ANEF)** ซึ่งทำหน้าที่เป็นเกณฑ์พื้นฐานสำหรับการออกแบบ การตัดสินใจ การพัฒนา การตรวจสอบ และการเปลี่ยนแปลง Framework ทุกส่วน

ค่านิยมหลักไม่ใช่เพียงคำประกาศเชิงนโยบาย แต่เป็นหลักที่ต้องสามารถตรวจสอบย้อนกลับไปยังข้อกำหนด สถาปัตยกรรม กระบวนการ และผลลัพธ์ของโครงการได้

---

## 2. Scope

เอกสารนี้ครอบคลุม

- ค่านิยมหลักของ ANEF
- ความหมายเชิงปฏิบัติของแต่ละค่านิยม
- พฤติกรรมที่คาดหวังจากบุคคล ทีม และระบบ
- เกณฑ์สำหรับประเมินความสอดคล้อง
- ความสัมพันธ์ระหว่างค่านิยมกับเอกสาร Constitution และ Design Principles

เอกสารนี้ไม่กำหนดรายละเอียดเชิงเทคนิคเฉพาะของภาษาโปรแกรม Framework ฐานข้อมูล Cloud หรือ AI Provider

---

## 3. Normative Language

คำต่อไปนี้ใช้ในความหมายเชิงข้อกำหนด

- **ต้อง (MUST):** เป็นข้อกำหนดบังคับ
- **ต้องไม่ (MUST NOT):** เป็นข้อห้ามบังคับ
- **ควร (SHOULD):** เป็นแนวทางที่ควรปฏิบัติ เว้นแต่มีเหตุผลที่บันทึกไว้อย่างชัดเจน
- **อาจ (MAY):** เป็นทางเลือกที่อนุญาต

---

## 4. Core Value Model

ค่านิยมของ ANEF แบ่งออกเป็น 4 กลุ่ม

```text
Direction Values
    ├── Long-term First
    └── Purpose before Activity

Trust Values
    ├── One Source of Truth
    ├── Evidence and Traceability
    └── Transparency

Engineering Values
    ├── Architecture before Implementation
    ├── Modularity
    ├── Quality Continuously
    └── Security and Privacy by Design

Collaboration Values
    ├── AI-Assisted, Human-Governed
    ├── Documentation Never Lags Behind
    └── Respectful and Inclusive Collaboration
```

---

## 5. Core Values

### 5.1 Long-term First

ทุกการตัดสินใจต้องพิจารณาผลกระทบระยะยาวก่อนความสะดวกเฉพาะหน้า

การตัดสินใจควรประเมินอย่างน้อย

- ความสามารถในการดูแลรักษา
- ความสามารถในการขยาย
- ต้นทุนการเปลี่ยนแปลงในอนาคต
- ความเข้ากันได้ย้อนหลัง
- ความเสี่ยงจากการผูกกับเทคโนโลยีหรือผู้ให้บริการ
- ภาระด้านเอกสารและการปฏิบัติการ

**พฤติกรรมที่คาดหวัง**

- เลือกโครงสร้างที่อธิบายและทดสอบได้
- ไม่สร้างหนี้ทางเทคนิคโดยไม่มีเจ้าของและแผนชำระ
- บันทึกเหตุผลเมื่อเลือกทางลัด
- ออกแบบ Migration Path สำหรับการเปลี่ยนแปลงสำคัญ

**Anti-patterns**

- เลือกเทคโนโลยีเพียงเพราะเป็นกระแส
- แก้ปัญหาเฉพาะหน้าโดยทำลาย Boundary ของระบบ
- เพิ่มความซับซ้อนโดยไม่มีคุณค่าที่วัดได้

---

### 5.2 Purpose before Activity

ทุกงานต้องเชื่อมโยงกับวัตถุประสงค์ ผลลัพธ์ หรือความเสี่ยงที่ต้องจัดการ

ANEF ไม่สนับสนุนการเพิ่มเอกสาร กระบวนการ หรือเทคโนโลยีเพียงเพื่อให้ดูครบถ้วน

**ข้อกำหนด**

- งานสำคัญต้องระบุ Outcome ที่ต้องการ
- เอกสารต้องมี Purpose และ Scope
- Metric ต้องเชื่อมโยงกับการตัดสินใจ
- Automation ต้องลดข้อผิดพลาด เวลา หรือภาระงานที่พิสูจน์ได้

---

### 5.3 One Source of Truth

ข้อมูล ข้อกำหนด และตรรกะหลักแต่ละเรื่องต้องมีเจ้าของและแหล่งอ้างอิงหลักที่ชัดเจน

การทำสำเนาเพื่ออ่านหรือประมวลผลอาจทำได้ แต่สำเนาต้องไม่กลายเป็นแหล่งแก้ไขอิสระโดยไม่มีระบบ Synchronization

**ข้อกำหนด**

- Domain Rule ต้องมี Canonical Owner
- API Contract ต้องมี Specification หลัก
- Schema ต้องมีเวอร์ชันและเจ้าของ
- เอกสารสรุปต้องอ้างอิงเอกสารต้นทาง
- Derived Data ต้องระบุแหล่งที่มาและเวลาอัปเดต

---

### 5.4 Evidence and Traceability

การเปลี่ยนแปลงที่มีนัยสำคัญต้องมีหลักฐานรองรับและติดตามย้อนกลับได้

หลักฐานอาจประกอบด้วย

- Requirement
- Architecture Decision Record (ADR)
- Test Result
- Threat Model
- Benchmark
- Incident Report
- User Research
- Operational Metric

**ข้อกำหนด**

- การตัดสินใจเชิงสถาปัตยกรรมต้องบันทึกเหตุผล
- การเปลี่ยนแปลงข้อกำหนดต้องเชื่อมโยงกับ Issue หรือ Decision Record
- Release ต้องระบุสิ่งที่เปลี่ยนและผลกระทบ
- ข้อยกเว้นต้องมีผู้อนุมัติ เหตุผล และวันทบทวน

---

### 5.5 Transparency

โครงสร้าง การตัดสินใจ ข้อจำกัด และความเสี่ยงต้องสามารถอธิบายแก่ผู้มีส่วนเกี่ยวข้องที่ได้รับสิทธิ์

Transparency ไม่ได้หมายถึงการเปิดเผยข้อมูลลับ แต่หมายถึงการหลีกเลี่ยงระบบที่ไม่มีผู้ใดเข้าใจหรือรับผิดชอบได้

**พฤติกรรมที่คาดหวัง**

- แยกข้อเท็จจริง สมมติฐาน และข้อเสนอแนะออกจากกัน
- ระบุความไม่แน่นอน
- เปิดเผยข้อจำกัดของระบบและโมเดล
- รายงานความล้มเหลวโดยไม่บิดเบือนข้อมูล

---

### 5.6 Architecture before Implementation

การพัฒนาต้องเริ่มจากความเข้าใจขอบเขต เจ้าของข้อมูล Interface และผลกระทบก่อนลงรายละเอียดการติดตั้ง

ข้อกำหนดนี้ไม่ได้บังคับให้ทุกงานต้องมีเอกสารขนาดใหญ่ แต่ต้องมีระดับการออกแบบที่เหมาะสมกับความเสี่ยง

**ขั้นต่ำที่ต้องมี**

- เป้าหมายและขอบเขต
- System Boundary
- เจ้าของข้อมูลและตรรกะ
- Interface ที่ได้รับผลกระทบ
- ความเสี่ยงสำคัญ
- วิธีตรวจสอบผลลัพธ์

---

### 5.7 Modularity

ระบบต้องแบ่งความรับผิดชอบออกเป็นส่วนที่มี Boundary ชัดเจน เชื่อมต่อผ่าน Contract และสามารถเปลี่ยนแปลงได้โดยลดผลกระทบต่อส่วนอื่น

**ข้อกำหนด**

- โมดูลต้องมีหน้าที่หลักที่ชัดเจน
- Dependency ต้องมีทิศทางที่ควบคุมได้
- Implementation Detail ต้องไม่รั่วผ่าน Public Interface
- Shared Component ต้องมีเจ้าของและนโยบายเวอร์ชัน
- Cross-module Change ต้องได้รับการประเมินผลกระทบ

---

### 5.8 Quality Continuously

คุณภาพไม่ใช่ขั้นตอนสุดท้าย แต่เป็นส่วนหนึ่งของทุก Increment

คุณภาพครอบคลุม

- Correctness
- Reliability
- Security
- Performance
- Accessibility
- Maintainability
- Operability
- Documentation Quality

**ข้อกำหนด**

- ทุกการเปลี่ยนแปลงต้องมีวิธีตรวจสอบที่เหมาะสม
- Defect ที่เกิดซ้ำควรนำไปสู่การปรับปรุงระบบหรือกระบวนการ
- Quality Gate ต้องสัมพันธ์กับระดับความเสี่ยง
- Test ต้องเน้นพฤติกรรมและ Contract ไม่ผูกกับ Implementation เกินจำเป็น

---

### 5.9 Security and Privacy by Design

ความปลอดภัยและความเป็นส่วนตัวต้องถูกพิจารณาตั้งแต่เริ่มออกแบบ ไม่ใช่เพิ่มภายหลัง

**ข้อกำหนด**

- ใช้หลัก Least Privilege
- เก็บข้อมูลเท่าที่จำเป็น
- ปกป้อง Secret และ Credential
- กำหนด Trust Boundary
- บันทึกเหตุการณ์ที่จำเป็นต่อการตรวจสอบ
- มีแนวทาง Backup, Recovery และ Incident Response
- ประเมินผลกระทบต่อข้อมูลส่วนบุคคลเมื่อเกี่ยวข้อง

---

### 5.10 AI-Assisted, Human-Governed

AI เป็นสมาชิกสนับสนุนของทีม แต่ความรับผิดชอบและอำนาจกำกับดูแลขั้นสุดท้ายยังอยู่กับมนุษย์หรือกลไก Governance ที่กำหนดไว้

**ข้อกำหนด**

- Output จาก AI ที่มีผลกระทบสูงต้องมีการตรวจสอบตามระดับความเสี่ยง
- AI ต้องไม่ข้าม Permission หรือ Approval Boundary
- การดำเนินการที่ย้อนกลับยากต้องมี Confirmation หรือ Policy ที่ชัดเจน
- ต้องเก็บหลักฐานที่จำเป็นต่อการ Audit โดยไม่เก็บข้อมูลเกินความจำเป็น
- ต้องสามารถปิด เปลี่ยน หรือแทนที่ AI Provider ได้เมื่อ Architecture กำหนดให้เป็น Vendor Neutral

---

### 5.11 Documentation Never Lags Behind

เอกสารต้องเปลี่ยนไปพร้อมกับระบบและข้อกำหนด

**ข้อกำหนด**

- Code, Contract และ Documentation ที่เกี่ยวข้องต้องอัปเดตใน Change Set เดียวกันเมื่อเหมาะสม
- เอกสารต้องระบุเวอร์ชันหรือสถานะ
- เอกสารที่ล้าสมัยต้องแก้ไข ทำเครื่องหมาย Deprecated หรือเก็บ Archive
- Diagram ต้องสอดคล้องกับ Architecture ปัจจุบัน
- README ต้องสะท้อนวิธีใช้งานจริง

---

### 5.12 Respectful and Inclusive Collaboration

ANEF สนับสนุนการทำงานร่วมกันที่เคารพ เห็นต่างได้อย่างมีเหตุผล และเปิดโอกาสให้ผู้เกี่ยวข้องเข้าถึงความรู้ที่จำเป็น

**ข้อกำหนด**

- วิจารณ์งาน ไม่โจมตีบุคคล
- การตัดสินใจต้องพิจารณาความเห็นจากบทบาทที่ได้รับผลกระทบ
- ภาษาและเอกสารควรชัดเจน ลดคำเฉพาะที่ไม่จำเป็น
- Accessibility ต้องเป็นส่วนหนึ่งของ Definition of Quality

---

## 6. Conflict Resolution Order

เมื่อค่านิยมเกิดความขัดแย้ง ให้ใช้ลำดับการพิจารณาดังนี้

1. ความปลอดภัย กฎหมาย และสิทธิของผู้ใช้
2. ความถูกต้องและความน่าเชื่อถือ
3. ความสามารถในการย้อนกลับและควบคุมความเสียหาย
4. เป้าหมายระยะยาวและความสามารถในการดูแลรักษา
5. ความเร็วและความสะดวกในการส่งมอบ

การเลือกที่ขัดกับลำดับนี้ต้องมีเหตุผล หลักฐาน ผู้อนุมัติ และระยะเวลาทบทวน

---

## 7. Value-to-Practice Mapping

| Core Value | Practice |
|---|---|
| Long-term First | ADR, Migration Plan, Deprecation Policy |
| One Source of Truth | Canonical Schema, Contract Registry, Ownership Map |
| Evidence and Traceability | Tests, Decision Logs, Audit Records |
| Architecture before Implementation | Design Review, Boundary Definition |
| Modularity | Dependency Rules, Interface Contracts |
| Quality Continuously | CI Quality Gates, Automated Tests |
| Security and Privacy by Design | Threat Modeling, Least Privilege |
| AI-Assisted, Human-Governed | Approval Gates, Risk Classification |
| Documentation Never Lags Behind | Docs-as-Code, Same-change Updates |
| Transparency | Status, Assumptions, Limitations, Risk Logs |

---

## 8. Conformance Requirements

โครงการที่ประกาศว่าใช้ ANEF ต้อง

1. ระบุค่านิยมที่นำไปใช้และข้อยกเว้น
2. กำหนดเจ้าของการกำกับดูแล
3. มีหลักฐานว่าข้อกำหนดสำคัญถูกแปลงเป็นกระบวนการหรือ Quality Gate
4. ทบทวนความสอดคล้องเมื่อ Architecture หรือความเสี่ยงเปลี่ยนแปลง
5. ไม่ใช้ชื่อ ANEF เพื่ออ้างคุณภาพโดยไม่มีหลักฐานสนับสนุน

---

## 9. Review Checklist

- [ ] การตัดสินใจนี้สอดคล้องกับเป้าหมายระยะยาวหรือไม่
- [ ] มีเจ้าของข้อมูลและตรรกะที่ชัดเจนหรือไม่
- [ ] มีหลักฐานและ Traceability เพียงพอหรือไม่
- [ ] Boundary และ Contract ถูกกำหนดหรือไม่
- [ ] Security และ Privacy ถูกพิจารณาตั้งแต่ต้นหรือไม่
- [ ] มีวิธีทดสอบ ตรวจสอบ และย้อนกลับหรือไม่
- [ ] เอกสารได้รับการอัปเดตพร้อมการเปลี่ยนแปลงหรือไม่
- [ ] บทบาทของ AI และผู้อนุมัติชัดเจนหรือไม่
- [ ] ผู้ได้รับผลกระทบสามารถเข้าใจข้อจำกัดและความเสี่ยงหรือไม่

---

## 10. Anti-Patterns

- Values เป็นคำโฆษณาแต่ไม่มีข้อกำหนดเชิงปฏิบัติ
- เอกสารกับระบบจริงไม่ตรงกัน
- ใช้ AI เพื่อข้ามการรีวิวหรือสิทธิ์อนุมัติ
- มีข้อมูลจริงหลายชุดโดยไม่มี Canonical Owner
- เพิ่มเครื่องมือและกระบวนการโดยไม่มี Outcome
- ยอมรับความเสี่ยงโดยไม่ระบุเจ้าของและวันทบทวน
- บังคับใช้มาตรฐานเดียวกับทุกงานโดยไม่พิจารณาระดับความเสี่ยง

---

## 11. Cross References

- ANEF-001 — Project Overview
- ANEF-002 — Vision
- ANEF-003 — Mission
- ANEF-005 — Constitution
- ANEF-006 — Design Principles
- ANEF-009 — Documentation Standard
- ANEF-010 — Versioning

---

## 12. Revision History

| Version | Date | Status | Description |
|---|---|---|---|
| 1.0 Draft | 2026-08-05 | Draft | Initial Core Values specification |
