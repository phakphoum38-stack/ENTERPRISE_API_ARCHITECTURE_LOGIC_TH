# ANEF-007 — Enterprise Glossary

| Field | Value |
|---|---|
| Document ID | ANEF-007 |
| Part | Part 1 — Foundation |
| Version | 1.0 Draft |
| Status | Draft |
| Owner | ANEF Working Group |
| Classification | Public |
| Depends On | ANEF-001 ถึง ANEF-006 |
| Next Document | ANEF-008 — Naming Standard |

## 1. Purpose

เอกสารฉบับนี้กำหนดคำศัพท์มาตรฐานที่ใช้ภายใน AI Native Enterprise Framework (ANEF) เพื่อสร้างความเข้าใจร่วมกัน ลดความกำกวม และทำให้เอกสาร สถาปัตยกรรม ตัวอย่าง เทมเพลต และเครื่องมือตรวจสอบใช้ภาษาเดียวกัน

## 2. Scope

Glossary นี้ใช้กับเอกสารและองค์ประกอบทั้งหมดของ ANEF ได้แก่ Specifications, Architecture Documents, ADRs, Templates, Examples, Checklists, Reference Implementations และ Validation Rules

## 3. Normative Language

คำสำคัญต่อไปนี้ใช้ในความหมายเชิงบรรทัดฐาน

- **MUST / SHALL — ต้อง:** ข้อกำหนดบังคับ
- **MUST NOT / SHALL NOT — ห้าม:** ข้อห้ามบังคับ
- **SHOULD — ควร:** แนวทางที่แนะนำอย่างยิ่ง หากไม่ปฏิบัติต้องมีเหตุผล
- **SHOULD NOT — ไม่ควร:** แนวทางที่ควรหลีกเลี่ยง เว้นแต่มีเหตุผลรองรับ
- **MAY — สามารถ:** ทางเลือกที่อนุญาต

## 4. General Requirements

### REQ-TERM-0001

เอกสารเชิงบรรทัดฐานทุกฉบับ **MUST** ใช้คำศัพท์ตาม ANEF-007

### REQ-TERM-0002

คำศัพท์ใหม่ **MUST** มีคำจำกัดความที่ไม่ซ้ำและไม่ขัดแย้งกับคำศัพท์เดิม

### REQ-TERM-0003

คำศัพท์ที่เลิกใช้ **MUST NOT** ถูกลบทิ้งโดยไม่มีบันทึกการทดแทนและเวอร์ชันที่เริ่มเลิกใช้

### REQ-TERM-0004

คำศัพท์ที่มีความหมายใกล้กัน **MUST** ระบุความแตกต่างอย่างชัดเจน

### REQ-TERM-0005

คำศัพท์ใหม่ **MUST** ผ่าน Editorial Review ก่อนใช้งานใน Specification อื่น

---

# 5. Foundation Terms

## TERM-0001 — Architecture

โครงสร้างระดับสูงของระบบ ซึ่งอธิบายองค์ประกอบ ความสัมพันธ์ ขอบเขต หลักการ และข้อจำกัดที่ใช้กำกับการออกแบบและวิวัฒนาการของระบบ

**Related:** System, Component, Boundary, Design

## TERM-0002 — System

ชุดขององค์ประกอบที่ทำงานร่วมกันเพื่อบรรลุวัตถุประสงค์ที่กำหนด ภายใต้ขอบเขตและสภาพแวดล้อมที่ชัดเจน

**Rule:** System **MUST** มี Scope และ Owner

## TERM-0003 — Component

หน่วยเชิงตรรกะหรือกายภาพที่มีความรับผิดชอบชัดเจนและสื่อสารกับองค์ประกอบอื่นผ่าน Contract หรือ Interface

## TERM-0004 — Module

กลุ่มของ Components ที่รวมกันตาม Capability, Domain หรือความรับผิดชอบร่วม

**Rule:** Module **MUST** มี Boundary และ Public Interface ที่ชัดเจน

## TERM-0005 — Boundary

ขอบเขตที่กำหนด Ownership, Responsibility, Data และ Contract ระหว่างองค์ประกอบหรือระบบ

## TERM-0006 — Responsibility

หน้าที่หลักที่องค์ประกอบหนึ่งต้องรับผิดชอบและสามารถตรวจสอบได้

## TERM-0007 — Ownership

ความรับผิดชอบที่ชัดเจนต่อข้อมูล การตัดสินใจ การเปลี่ยนแปลง และคุณภาพขององค์ประกอบหนึ่ง

## TERM-0008 — Interface

สัญญาที่กำหนดวิธีการสื่อสารระหว่างองค์ประกอบโดยไม่เปิดเผยรายละเอียดภายใน

## TERM-0009 — Contract

ข้อตกลงที่กำหนด Inputs, Outputs, Preconditions, Postconditions, Errors, Compatibility และ Lifecycle

**Rule:** Contract **MUST** มี Version เมื่อถูกใช้ข้าม Boundary

## TERM-0010 — Dependency

ความสัมพันธ์ที่องค์ประกอบหนึ่งต้องอาศัยอีกองค์ประกอบหนึ่งเพื่อทำงาน

---

# 6. Architecture Terms

## TERM-0011 — Layer

การแบ่งระบบเชิงตรรกะตามหน้าที่และทิศทาง Dependency

## TERM-0012 — Domain

ขอบเขตของปัญหา ความรู้ กฎ และภาษาทางธุรกิจที่ระบบถูกสร้างขึ้นเพื่อรองรับ

## TERM-0013 — Bounded Context

ขอบเขตที่ Model และคำศัพท์ชุดหนึ่งมีความหมายสอดคล้องกันและมี Contract ชัดเจนเมื่อติดต่อกับ Context อื่น

## TERM-0014 — Entity

วัตถุใน Domain ที่มี Identity ต่อเนื่อง แม้ Attribute จะเปลี่ยนแปลง

## TERM-0015 — Value Object

วัตถุที่นิยามด้วยค่าภายใน ไม่ใช่ Identity และควรเป็น Immutable เมื่อเหมาะสม

## TERM-0016 — Aggregate

กลุ่ม Entity และ Value Object ที่ถูกจัดการเป็นหน่วย Transactional Consistency เดียว

## TERM-0017 — Aggregate Root

Entity หลักที่เป็นจุดเข้าถึง Aggregate และรับผิดชอบการรักษา Invariants

## TERM-0018 — Invariant

เงื่อนไขที่ต้องเป็นจริงเสมอภายในขอบเขตที่กำหนด

## TERM-0019 — Service

องค์ประกอบที่ให้ Capability หรือดำเนินงานที่ไม่เหมาะจะอยู่ใน Entity หรือ Value Object

## TERM-0020 — Repository

Abstraction สำหรับจัดเก็บและเรียกคืน Aggregate หรือ Domain Object โดยซ่อนรายละเอียด Storage

## TERM-0021 — Adapter

องค์ประกอบที่แปลง Protocol, Data หรือ Interface ระหว่างสองขอบเขต

**Rule:** Adapter **SHOULD NOT** มี Business Logic

## TERM-0022 — Gateway

จุดเชื่อมต่อที่ควบคุมการสื่อสารกับระบบหรือบริการภายนอก

## TERM-0023 — Use Case

ลำดับการทำงานระดับ Application ที่บรรลุเป้าหมายหนึ่งของ Actor หรือระบบ

## TERM-0024 — Orchestrator

องค์ประกอบที่ประสานหลายขั้นตอนหรือบริการตาม Workflow โดยไม่ครอบครอง Business Rules ที่เป็นของ Domain

## TERM-0025 — Composition Root

ตำแหน่งที่ระบบประกอบ Dependencies และเลือก Implementations สำหรับ Runtime

---

# 7. Business and Governance Terms

## TERM-0026 — Business Capability

ความสามารถที่องค์กรต้องมีเพื่อบรรลุภารกิจ โดยไม่ผูกกับโครงสร้างทีม เทคโนโลยี หรือ Implementation

## TERM-0027 — Business Rule

เงื่อนไขหรือข้อกำหนดที่กำกับการตัดสินใจและพฤติกรรมทางธุรกิจ

## TERM-0028 — Policy

ข้อกำหนดระดับองค์กรหรือระบบที่กำหนดแนวทางการตัดสินใจ การควบคุม หรือการดำเนินงาน

## TERM-0029 — Process

ชุดกิจกรรมและ Workflow ที่จัดการร่วมกันเพื่อสร้างผลลัพธ์ทางธุรกิจ

## TERM-0030 — Workflow

ลำดับกิจกรรม สถานะ เงื่อนไข และการเปลี่ยนผ่านที่นำไปสู่ผลลัพธ์หนึ่ง

## TERM-0031 — Actor

บุคคล ระบบ หรือบริการที่มีปฏิสัมพันธ์กับระบบในบทบาทหนึ่ง

## TERM-0032 — Role

ชุดความรับผิดชอบและสิทธิ์ที่กำหนดให้ Actor โดยแยกจากตัวบุคคล

## TERM-0033 — Stakeholder

บุคคลหรือหน่วยงานที่มีผลประโยชน์ มีอำนาจตัดสินใจ หรือได้รับผลกระทบจากระบบ

## TERM-0034 — Requirement

ข้อกำหนดที่ระบุสิ่งที่ระบบ เอกสาร หรือกระบวนการต้องทำหรือคุณสมบัติที่ต้องมี

**Rule:** Requirement **MUST** มี Identifier และวิธีตรวจสอบ

## TERM-0035 — Constraint

ข้อจำกัดที่มีผลต่อการออกแบบ การพัฒนา การติดตั้ง หรือการดำเนินงาน

## TERM-0036 — Assumption

เงื่อนไขที่ถือว่าเป็นจริงชั่วคราวเพื่อใช้ในการวางแผนหรือออกแบบ และต้องได้รับการทบทวนเมื่อมีข้อมูลใหม่

## TERM-0037 — Risk

เหตุการณ์หรือเงื่อนไขที่ไม่แน่นอนซึ่งอาจส่งผลต่อเป้าหมาย คุณภาพ ความปลอดภัย ต้นทุน หรือเวลา

## TERM-0038 — Rationale

เหตุผลและหลักฐานที่รองรับการตัดสินใจ ข้อกำหนด หรือมาตรฐาน

## TERM-0039 — Traceability

ความสามารถในการติดตามความสัมพันธ์ระหว่าง Requirement, Decision, Architecture, Implementation, Test และ Operation

## TERM-0040 — Conformance

ระดับที่องค์ประกอบหนึ่งปฏิบัติตามข้อกำหนดของมาตรฐานหรือ Specification

---

# 8. AI Terms

## TERM-0041 — Artificial Intelligence (AI)

ระบบหรือความสามารถเชิงคำนวณที่ประมวลผลข้อมูลเพื่อสร้างการคาดการณ์ การจำแนก การให้เหตุผล คำแนะนำ การตัดสินใจ หรือผลลัพธ์ที่สร้างขึ้น

## TERM-0042 — Model

สิ่งประดิษฐ์เชิงคำนวณที่เรียนรู้หรือกำหนดความสัมพันธ์ระหว่าง Input และ Output

**Rule:** Model **MUST** มี Version และ Provenance ที่เพียงพอสำหรับการตรวจสอบ

## TERM-0043 — Inference

กระบวนการใช้ Model เพื่อสร้าง Output จาก Input

## TERM-0044 — Prompt

คำสั่ง บริบท ข้อมูล หรือข้อจำกัดที่ส่งให้ระบบ AI เพื่อกำหนดงานและรูปแบบผลลัพธ์

## TERM-0045 — Context

ข้อมูลที่เกี่ยวข้องกับการตีความ การวางแผน หรือการตัดสินใจในช่วงเวลาหนึ่ง

## TERM-0046 — Memory

กลไกที่เก็บและเรียกคืนข้อมูลจาก Interaction หรือ State ก่อนหน้าเพื่อใช้ภายหลัง

## TERM-0047 — Knowledge Base

แหล่งข้อมูลที่มีโครงสร้างหรือไม่มีโครงสร้างซึ่งใช้เป็นฐานสำหรับ Retrieval, Reasoning หรือ Validation

## TERM-0048 — Retrieval

กระบวนการค้นหาและนำข้อมูลที่เกี่ยวข้องจากแหล่งความรู้มาใช้

## TERM-0049 — Reasoning

กระบวนการเชื่อมโยงข้อมูล กฎ ข้อจำกัด และหลักฐานเพื่อสร้างข้อสรุปหรือทางเลือก

## TERM-0050 — Planning

กระบวนการแปลง Goal ให้เป็น Tasks, Dependencies, Priorities และ Execution Order

## TERM-0051 — AI Agent

องค์ประกอบซอฟต์แวร์ที่รับ Goal ใช้ Context และ Policy เพื่อวางแผน เรียกใช้ Tools และสร้างผลลัพธ์ภายในขอบเขตที่ได้รับอนุญาต

## TERM-0052 — Tool

ความสามารถภายนอก Model ที่ Agent หรือระบบ AI เรียกใช้เพื่ออ่านข้อมูล คำนวณ หรือดำเนินการ

## TERM-0053 — Guardrail

ข้อจำกัด การตรวจสอบ หรือ Control ที่ป้องกันพฤติกรรมหรือผลลัพธ์ที่ไม่อนุญาต

## TERM-0054 — Human-in-the-Loop

รูปแบบที่มนุษย์มีบทบาทตรวจสอบ อนุมัติ แก้ไข หรือหยุดการทำงานของระบบ AI ในจุดที่กำหนด

## TERM-0055 — AI Output

ผลลัพธ์ที่สร้างโดยระบบ AI และอาจต้องผ่าน Validation ตามระดับความเสี่ยง

---

# 9. API and Platform Terms

## TERM-0056 — API

ชุด Interface และ Contract สำหรับการสื่อสารระหว่างซอฟต์แวร์

## TERM-0057 — Endpoint

จุดที่เปิดให้เรียกใช้ Operation หรือ Resource ผ่าน API

## TERM-0058 — Request

ข้อมูลและ Metadata ที่ผู้เรียกส่งเข้าสู่ API

## TERM-0059 — Response

ผลลัพธ์ สถานะ และ Metadata ที่ API ส่งกลับ

## TERM-0060 — Payload

ข้อมูลหลักที่ถูกส่งภายใน Message, Request, Response หรือ Event

## TERM-0061 — Protocol

กฎ รูปแบบ และลำดับที่กำหนดการสื่อสารระหว่างระบบ

## TERM-0062 — Transport

กลไกที่ใช้ส่งข้อมูลระหว่างจุดสื่อสาร

## TERM-0063 — Platform

ชุด Runtime, Services, Interfaces และ Operational Capabilities ที่รองรับ Applications หรือ Workloads

## TERM-0064 — Runtime

สภาพแวดล้อมและองค์ประกอบที่ทำให้ซอฟต์แวร์ทำงานจริง

## TERM-0065 — Environment

บริบทที่แยก Configurations, Resources, Data และ Deployment เช่น Development, Test, Staging และ Production

## TERM-0066 — Configuration

ข้อมูลที่กำหนดพฤติกรรมของระบบโดยไม่แก้ Source Code

## TERM-0067 — Feature Flag

Configuration ที่เปิด ปิด หรือควบคุมความสามารถของระบบแบบมีเงื่อนไข

## TERM-0068 — Artifact

ผลลัพธ์ที่สร้างจากกระบวนการ Build, Package, Documentation หรือ Release และสามารถระบุ Version ได้

## TERM-0069 — Deployment

กระบวนการนำ Artifact และ Configuration ไปติดตั้งหรือเปิดใช้งานใน Environment

## TERM-0070 — Release

ชุดการเปลี่ยนแปลงที่ได้รับ Version และอนุมัติให้เผยแพร่หรือใช้งาน

---

# 10. Data and Security Terms

## TERM-0071 — Data Owner

บทบาทที่รับผิดชอบความหมาย คุณภาพ การอนุญาต และ Lifecycle ของข้อมูลชุดหนึ่ง

## TERM-0072 — Schema

ข้อกำหนดโครงสร้าง ชนิดข้อมูล Constraints และความสัมพันธ์ของข้อมูล

## TERM-0073 — Record

หน่วยข้อมูลหนึ่งที่เป็นไปตาม Schema

## TERM-0074 — Projection

Representation ของข้อมูลที่สร้างจาก Source Model เพื่อรองรับ Query หรือ Use Case เฉพาะ

## TERM-0075 — Snapshot

ภาพสถานะของข้อมูลหรือระบบ ณ เวลาหนึ่ง

## TERM-0076 — Migration

การเปลี่ยน Data, Schema, Configuration หรือ Runtime จากสถานะหนึ่งไปอีกสถานะหนึ่งอย่างควบคุมได้

## TERM-0077 — Authentication

กระบวนการพิสูจน์ Identity

## TERM-0078 — Authorization

กระบวนการตัดสินว่า Identity ที่พิสูจน์แล้วมีสิทธิ์ดำเนินการใด

## TERM-0079 — Identity

ตัวแทนที่ใช้ระบุบุคคล บริการ อุปกรณ์ หรือระบบอย่างมีเอกลักษณ์

## TERM-0080 — Credential

ข้อมูลหรือกลไกที่ใช้พิสูจน์ Identity

## TERM-0081 — Secret

ข้อมูลที่ต้องปกป้องจากการเปิดเผยหรือใช้งานโดยไม่ได้รับอนุญาต

**Rule:** Secret **MUST NOT** ถูกบันทึกใน Source Repository แบบ Plaintext

## TERM-0082 — Token

ข้อมูลที่ออกให้เพื่อแสดงสิทธิ์ สถานะ หรือการอนุญาตในช่วงเวลาหนึ่ง

## TERM-0083 — Encryption

การแปลงข้อมูลให้อ่านไม่ได้โดยผู้ที่ไม่มี Key ที่เหมาะสม

## TERM-0084 — Audit Log

บันทึกเหตุการณ์ที่ออกแบบเพื่อการตรวจสอบย้อนหลังและต้องรักษาความถูกต้องเชิงหลักฐาน

## TERM-0085 — Threat

สาเหตุหรือเหตุการณ์ที่อาจสร้างความเสียหายต่อระบบ ข้อมูล หรือผู้ใช้งาน

## TERM-0086 — Vulnerability

จุดอ่อนที่ Threat สามารถใช้เพื่อสร้างผลกระทบ

## TERM-0087 — Control

มาตรการด้านกระบวนการ เทคนิค หรือองค์กรที่ลด Risk หรือบังคับ Policy

## TERM-0088 — Least Privilege

หลักการให้สิทธิ์เฉพาะเท่าที่จำเป็นต่อการทำงานและเฉพาะช่วงเวลาที่ต้องใช้

---

# 11. Documentation and Lifecycle Terms

## TERM-0089 — Specification

เอกสารเชิงบรรทัดฐานที่กำหนด Requirements, Rules, Interfaces หรือ Constraints

## TERM-0090 — Standard

ข้อกำหนดหรือแนวปฏิบัติที่ได้รับการอนุมัติให้ใช้ร่วมกันภายในขอบเขตหนึ่ง

## TERM-0091 — Guideline

คำแนะนำที่ไม่บังคับ แต่ช่วยให้ตัดสินใจหรือปฏิบัติงานสอดคล้องกับหลักการ

## TERM-0092 — Reference

เอกสาร ข้อมูล หรือตัวอย่างที่สนับสนุนความเข้าใจ แต่ไม่สร้าง Requirement ใหม่โดยอัตโนมัติ

## TERM-0093 — Template

โครงสร้างเริ่มต้นที่กำหนดรูปแบบและช่องข้อมูลสำหรับสร้าง Artifact อย่างสม่ำเสมอ

## TERM-0094 — Example

กรณีสาธิตที่แสดงวิธีประยุกต์ Specification โดยไม่แทนที่ข้อกำหนดหลัก

## TERM-0095 — Checklist

รายการตรวจสอบที่ช่วยยืนยันว่าขั้นตอนหรือ Requirement ถูกพิจารณาครบ

## TERM-0096 — Draft

สถานะเอกสารที่ยังเปลี่ยนแปลงได้และยังไม่ถือเป็น Baseline ที่อนุมัติ

## TERM-0097 — Approved

สถานะเอกสารที่ผ่าน Review และ Approval ตาม Governance ที่กำหนด

## TERM-0098 — Deprecated

สถานะที่ยังคงไว้เพื่อ Compatibility แต่ไม่แนะนำสำหรับงานใหม่

## TERM-0099 — Archived

สถานะที่หยุดใช้งานและเก็บไว้เพื่อประวัติหรือการตรวจสอบ

## TERM-0100 — Revision History

บันทึก Version, Date, Author/Owner และคำอธิบายการเปลี่ยนแปลงของเอกสาร

---

# 12. Reserved and Discouraged Names

ชื่อทั่วไปต่อไปนี้ **SHOULD NOT** ใช้เป็นชื่อ Component, Module หรือ Service โดยไม่มีคำขยายที่สื่อความหมายชัดเจน

- `Common`
- `General`
- `Global`
- `Helper`
- `Manager`
- `Misc`
- `Shared`
- `Temp`
- `Utils`

การใช้คำเหล่านี้เป็นส่วนประกอบของชื่อ **MAY** ทำได้เมื่อมีขอบเขตชัดเจน เช่น `DateParsingUtilities` แต่ชื่อ `Utils` เพียงอย่างเดียวไม่ผ่านมาตรฐาน

# 13. Deprecated-Term Rules

### RULE-TERM-0101

คำศัพท์ที่เปลี่ยนเป็น Deprecated **MUST** ระบุ Replacement Term

### RULE-TERM-0102

เอกสารใหม่ **MUST NOT** ใช้ Deprecated Term เว้นแต่กล่าวถึง Compatibility หรือ Migration

### RULE-TERM-0103

Deprecated Term **MUST** ระบุ Version ที่เริ่มเลิกใช้

# 14. Identifier Prefixes

| Prefix | Purpose |
|---|---|
| TERM | Glossary Term |
| REQ | Requirement |
| RULE | Rule |
| PRN | Principle |
| ADR | Architecture Decision Record |
| ARCH | Architecture Element |
| PAT | Pattern |
| ANTI | Anti-pattern |
| EX | Example |
| CHK | Checklist |
| API | API Definition |
| EVT | Event Definition |
| VAL | Validation Rule |
| DGM | Diagram |

# 15. Compliance Checklist

- [ ] คำศัพท์เชิงเทคนิคใช้ความหมายตาม ANEF-007
- [ ] คำศัพท์ใหม่มี Identifier และ Definition ที่ไม่ซ้ำ
- [ ] คำศัพท์ใกล้เคียงมีคำอธิบายความแตกต่าง
- [ ] Deprecated Terms มี Replacement และ Version
- [ ] เอกสารไม่สร้างคำจำกัดความซ้ำโดยไม่จำเป็น
- [ ] Examples และ Templates ใช้คำศัพท์มาตรฐาน

# 16. Cross References

- ANEF-001 — Project Overview
- ANEF-004 — Core Values
- ANEF-005 — Constitution
- ANEF-006 — Design Principles
- ANEF-008 — Naming Standard
- ANEF-009 — Documentation Standard
- ANEF-010 — Versioning

# 17. Revision History

| Version | Status | Description |
|---|---|---|
| 1.0 Draft | Draft | Initial enterprise glossary with 100 standardized terms |
