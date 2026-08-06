# ANEF-011 — Repository Structure

| Field | Value |
|---|---|
| Document ID | ANEF-011 |
| Title | Repository Structure |
| Version | 1.0.0-draft |
| Status | Draft |
| Category | Foundation |
| Owner | ANEF Working Group |
| Classification | Public |
| Depends On | ANEF-005, ANEF-006, ANEF-008, ANEF-009, ANEF-010 |

## 1. Purpose

เอกสารฉบับนี้กำหนดโครงสร้างมาตรฐานของ Repository สำหรับ AI Native Enterprise Framework (ANEF) และโปรเจกต์ที่นำ ANEF ไปใช้ เพื่อให้ Source Code, เอกสาร, Contract, Infrastructure, Security Evidence, Test Evidence และ Release Artifact มีตำแหน่งที่ชัดเจน ค้นหาได้ และตรวจสอบย้อนหลังได้

เป้าหมายคือทำให้ Repository เป็นแหล่งความจริงร่วมกันของมนุษย์ ระบบอัตโนมัติ และ AI โดยไม่ผูกติดกับภาษา Framework, Cloud Provider หรือแพลตฟอร์มใดแพลตฟอร์มหนึ่ง

## 2. Scope

มาตรฐานนี้ใช้กับ:

- Repository เอกสารมาตรฐาน ANEF
- Monorepo และ Multi-repository architecture
- Application, Service, Library และ Shared Platform
- API, Event, Schema และ Integration Contract
- Infrastructure as Code และ Deployment configuration
- AI instruction, prompt, evaluation และ governance artifact
- Security, Compliance, ADR, Test และ Release evidence

## 3. Normative Language

คำว่า **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT** และ **MAY** ใช้ตามนิยามใน ANEF-007

## 4. Core Principles

### 4.1 One Truth

ข้อมูลประเภทเดียวกัน **MUST** มีเจ้าของหลักและตำแหน่งอ้างอิงหลักเพียงแห่งเดียว ส่วนสำเนาที่สร้างเพื่อ Build หรือ Distribution ต้องระบุที่มาและสามารถสร้างใหม่ได้

### 4.2 Clear Boundaries

Domain, Application, Interface, Infrastructure และ Delivery concerns **SHOULD** ถูกแยกออกจากกันอย่างชัดเจน เพื่อให้เปลี่ยน UI, Database, AI Provider หรือ Deployment target ได้โดยไม่กระทบ Core Logic โดยไม่จำเป็น

### 4.3 Evidence by Default

การตัดสินใจสำคัญ การเปลี่ยน Contract การอนุมัติ Release และผลการทดสอบ **MUST** มีหลักฐานที่ค้นหาและอ้างอิงได้

### 4.4 Automation Friendly

ชื่อไฟล์ โครงสร้างไดเรกทอรี Metadata และ Contract **SHOULD** อยู่ในรูปแบบที่ CI/CD, Static Analysis, Code Generator และ AI Agent อ่านได้อย่างแน่นอน

### 4.5 History Preservation

Release, Snapshot และเอกสารที่อนุมัติแล้ว **MUST NOT** ถูกเขียนทับโดยไม่มี Version ใหม่และบันทึกการเปลี่ยนแปลง

## 5. Canonical Enterprise Repository Structure

โครงสร้างอ้างอิงมาตรฐาน:

```text
repository-root/
├── README.md
├── CHANGELOG.md
├── LICENSE
├── SECURITY.md
├── CONTRIBUTING.md
├── CODEOWNERS
├── .editorconfig
├── .gitignore
├── .github/
│   ├── workflows/
│   ├── ISSUE_TEMPLATE/
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── dependabot.yml
├── docs/
│   ├── architecture/
│   ├── adr/
│   ├── governance/
│   ├── operations/
│   ├── security/
│   └── user-guides/
├── contracts/
│   ├── api/
│   ├── events/
│   ├── schemas/
│   └── policies/
├── src/
│   ├── domain/
│   ├── application/
│   ├── interfaces/
│   └── infrastructure/
├── apps/
├── services/
├── packages/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   ├── end-to-end/
│   ├── performance/
│   └── security/
├── ai/
│   ├── instructions/
│   ├── prompts/
│   ├── evaluations/
│   ├── guardrails/
│   └── model-cards/
├── infra/
│   ├── environments/
│   ├── modules/
│   ├── policies/
│   └── migrations/
├── scripts/
├── tools/
├── evidence/
│   ├── reviews/
│   ├── tests/
│   ├── security/
│   └── releases/
└── releases/
```

โปรเจกต์ **MAY** ตัดส่วนที่ไม่ใช้ แต่ **MUST NOT** เปลี่ยนความหมายของโฟลเดอร์มาตรฐานโดยไม่มี ADR

## 6. Directory Responsibilities

### 6.1 `docs/`

เก็บเอกสารที่อธิบายเหตุผล การออกแบบ การกำกับดูแล และวิธีดำเนินงาน เอกสารเชิงสถาปัตยกรรมต้องอ้างอิง ADR หรือ Requirement ที่เกี่ยวข้อง

### 6.2 `contracts/`

เก็บสัญญาที่ระบบอื่นพึ่งพา เช่น OpenAPI, AsyncAPI, JSON Schema, Protobuf, GraphQL Schema, Policy Schema และ Compatibility declaration

Contract ที่เผยแพร่ภายนอก **MUST** มี Version, Owner และ Compatibility Policy

### 6.3 `src/`

เก็บ Core implementation โดยแนะนำการแยก:

- `domain/` — Business rules และ Domain model
- `application/` — Use case และ orchestration
- `interfaces/` — API, UI adapter, CLI และ external-facing adapter
- `infrastructure/` — Database, network, file system, provider integration

Domain layer **MUST NOT** ขึ้นกับ UI, Database driver หรือ Cloud SDK โดยตรง

### 6.4 `apps/`, `services/`, `packages/`

- `apps/` ใช้สำหรับ deployable user-facing applications
- `services/` ใช้สำหรับ independently deployable backend services
- `packages/` ใช้สำหรับ reusable libraries และ shared modules

แต่ละหน่วย **SHOULD** มี README, Owner, Test และ Build definition ของตนเอง

### 6.5 `tests/`

Test ต้องแยกตามระดับเพื่อให้ทราบขอบเขต ความเร็ว และความรับผิดชอบ ผลทดสอบที่ใช้อนุมัติ Release **SHOULD** ถูกเก็บหรือเชื่อมโยงใน `evidence/tests/`

### 6.6 `ai/`

เก็บ Artifact ที่ควบคุมพฤติกรรม AI ได้แก่ System instruction, Prompt template, Evaluation dataset, Guardrail, Tool contract และ Model card

Prompt ที่มีผลต่อ Production **MUST** ถูก Version และ Review เช่นเดียวกับ Source Code

### 6.7 `infra/`

เก็บ Infrastructure as Code, Environment definition, Policy และ Migration โดย Secret จริง **MUST NOT** ถูก Commit ลง Repository

### 6.8 `evidence/`

เก็บหรือเชื่อมโยงหลักฐานการ Review, Test, Security scan, Approval และ Release โดย Artifact ต้องมี Timestamp, Source และ Version ที่ตรวจสอบได้

## 7. ANEF Documentation Repository Structure

Repository มาตรฐาน ANEF ใช้รูปแบบเฉพาะ:

```text
.
├── README.md
├── CHANGELOG.md
├── VERSION_INDEX.md
├── current/
│   └── README.md
└── versions/
    └── vX.Y.Z[-status]/
        ├── README.md
        └── docs/
            ├── 00_FOUNDATION/
            ├── 01_GOVERNANCE/
            ├── 02_ARCHITECTURE/
            ├── 03_API_AND_INTEGRATION/
            ├── 04_DATA/
            ├── 05_AI_NATIVE/
            ├── 06_SECURITY/
            ├── 07_DELIVERY/
            ├── 08_OPERATIONS/
            └── 09_EVIDENCE_AND_COMPLIANCE/
```

`current/` เป็นตัวชี้สถานะการพัฒนา ส่วนเนื้อหาจริงของแต่ละเวอร์ชัน **MUST** อยู่ภายใต้ `versions/`

## 8. Repository Requirements

### REQ-REP-0001 — Root README

ทุก Repository **MUST** มี `README.md` ที่ระบุ Purpose, Scope, Owner, วิธีใช้งาน และสถานะโครงการ

### REQ-REP-0002 — Ownership

ส่วนสำคัญของ Repository **MUST** ระบุ Owner ผ่าน CODEOWNERS, Metadata หรือระบบที่เทียบเท่า

### REQ-REP-0003 — No committed secrets

Repository **MUST NOT** เก็บ Password, Token, Private Key หรือ Production credential ใน Source Control

### REQ-REP-0004 — Contract isolation

Public contract **MUST** แยกจาก implementation และต้องสามารถตรวจ Compatibility ได้

### REQ-REP-0005 — Reproducible automation

ขั้นตอน Build, Test และ Validation **SHOULD** รันซ้ำได้ด้วยคำสั่งหรือ Workflow ที่เก็บใน Repository

### REQ-REP-0006 — Traceable changes

การเปลี่ยนแปลงที่มีนัยสำคัญ **MUST** เชื่อมโยงกับ Issue, Requirement, ADR หรือ Change record

### REQ-REP-0007 — Protected releases

Release artifact และ Stable snapshot **MUST** เชื่อมโยงกับ Commit และ Version ที่แน่นอน

### REQ-REP-0008 — Generated content

ไฟล์ที่สร้างอัตโนมัติ **MUST** ระบุ Generator, Source และวิธีสร้างใหม่ หรือถูกเก็บนอก Source Tree ตามนโยบายของโปรเจกต์

### REQ-REP-0009 — AI artifact governance

AI instruction และ Prompt ที่ใช้ใน Production **MUST** มี Version, Owner, Review status และ Evaluation evidence

### REQ-REP-0010 — Boundary enforcement

Architecture boundary ที่ประกาศไว้ **SHOULD** ถูกตรวจด้วย Linter, Dependency rule หรือ CI test

## 9. Monorepo and Multi-repository Rules

### 9.1 Monorepo

เหมาะเมื่อทีมต้องการ Atomic change, Shared tooling และ Cross-component refactoring แต่ต้องมี Ownership, Dependency boundary และ Selective CI ที่ชัดเจน

### 9.2 Multi-repository

เหมาะเมื่อแต่ละ Service มี Lifecycle, Security boundary หรือ Release cadence ที่เป็นอิสระ แต่ต้องมี Contract registry, Version policy และ Cross-repository traceability

### 9.3 Selection Rule

องค์กร **SHOULD** เลือกรูปแบบจาก Ownership, Deployment independence, Compliance boundary และ Change coupling ไม่ใช่จากความนิยมของเครื่องมือ

## 10. Branching and Change Flow

รูปแบบแนะนำ:

```text
main
feature/<scope>
fix/<scope>
docs/<document-id>-<topic>
release/<version>
```

การเปลี่ยนแปลง **SHOULD** ผ่าน Pull Request และต้องมี:

1. Scope ที่ชัดเจน
2. เหตุผลและผลกระทบ
3. Validation หรือ Test evidence
4. Compatibility assessment
5. Documentation update เมื่อพฤติกรรมเปลี่ยน

## 11. Repository Health Checks

CI **SHOULD** ตรวจอย่างน้อย:

- Broken links
- Required metadata
- Duplicate Document ID หรือ Requirement ID
- Naming convention
- Secret scanning
- Dependency vulnerability
- Contract compatibility
- Architecture boundary
- Test result
- Changelog และ Version alignment

## 12. Anti-Patterns

- เก็บทุกอย่างไว้ในโฟลเดอร์เดียว
- ใช้ชื่อ `misc`, `temp`, `final2` หรือ `new-folder` เป็นโครงสร้างถาวร
- ผูก Domain logic กับ UI หรือ Database โดยตรง
- Commit Secret หรือไฟล์ Environment จริง
- เก็บ Prompt production โดยไม่มี Version และ Evaluation
- สร้างหลายแหล่งความจริงสำหรับ Contract เดียวกัน
- แก้ Stable snapshot โดยตรง
- มี Workflow ที่รันได้เฉพาะเครื่องของบุคคลใดบุคคลหนึ่ง

## 13. Adoption Checklist

- [ ] มี Root README และ Owner
- [ ] แยก Source, Contract, Test, Infrastructure และ Documentation
- [ ] มี Security และ Secret policy
- [ ] มี Build/Test command ที่รันซ้ำได้
- [ ] มี ADR สำหรับข้อยกเว้นเชิงสถาปัตยกรรม
- [ ] Contract มี Version และ Compatibility policy
- [ ] AI artifact มี Owner, Version และ Evaluation
- [ ] Release เชื่อมโยงกับ Commit และ Evidence
- [ ] CI ตรวจ Naming, Link, Secret และ Boundary
- [ ] ไม่มี Stable artifact ถูกเขียนทับ

## 14. Relationship to Other Documents

- ANEF-008 กำหนด Naming Standard
- ANEF-009 กำหนด Documentation Standard
- ANEF-010 กำหนด Versioning Standard
- ANEF-012 จะกำหนด Document Lifecycle
- ANEF-013 จะกำหนด Review Process
- ANEF-014 จะกำหนด Approval Workflow
- ANEF-015 จะกำหนด Change Management

## 15. Revision History

| Version | Date | Status | Change |
|---|---|---|---|
| 1.0.0-draft | 2026-08-06 | Draft | สร้างมาตรฐานโครงสร้าง Repository ฉบับแรก |

> Repository structure is architecture made visible.