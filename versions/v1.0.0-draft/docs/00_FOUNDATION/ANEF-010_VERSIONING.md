# ANEF-010 — Versioning Standard

| Field | Value |
|---|---|
| Document ID | ANEF-010 |
| Title | Versioning Standard |
| Version | 1.0.0-draft |
| Status | Draft |
| Category | Foundation |
| Owner | ANEF Working Group |
| Classification | Public |
| Depends On | ANEF-005, ANEF-007, ANEF-008, ANEF-009 |

## 1. Purpose

เอกสารฉบับนี้กำหนดมาตรฐานการกำหนดเวอร์ชัน การรักษาประวัติ ความเข้ากันได้ และการเผยแพร่เอกสาร ข้อกำหนด สัญญา และชุดเผยแพร่ภายใน AI Native Enterprise Framework (ANEF)

เป้าหมายคือทำให้ทุกการเปลี่ยนแปลงสามารถระบุ ตรวจสอบ อ้างอิง ย้อนกลับ และย้ายผ่านเวอร์ชันได้อย่างเป็นระบบ โดยไม่เขียนทับหลักฐานของเวอร์ชันเดิม

## 2. Scope

มาตรฐานนี้ใช้กับ:

- เวอร์ชันของ ANEF ทั้งชุด
- เวอร์ชันของเอกสารแต่ละฉบับ
- เวอร์ชันของ API, Schema, Event และ Contract
- Snapshot ในโฟลเดอร์ `versions/`
- Git tags และ GitHub releases
- Pre-release และ Draft releases
- Migration และ Compatibility declarations

รายละเอียดวงจรชีวิตเอกสารกำหนดเพิ่มเติมใน ANEF-012

## 3. Normative Language

คำว่า **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT** และ **MAY** ใช้ตามนิยามใน ANEF-007

## 4. Version Model

ANEF ใช้ Semantic Versioning ในรูปแบบ:

```text
MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]
```

ตัวอย่าง:

```text
1.0.0
1.1.0
1.1.1
2.0.0-rc.1
1.0.0-draft
1.0.0+build.20260806
```

### 4.1 MAJOR

เพิ่มค่า MAJOR เมื่อมีการเปลี่ยนแปลงที่ไม่เข้ากันกับเวอร์ชันเดิม หรือเปลี่ยนหลักการ/สัญญาที่ผู้ใช้เดิมไม่สามารถนำไปใช้ต่อได้โดยไม่ปรับแก้

### 4.2 MINOR

เพิ่มค่า MINOR เมื่อเพิ่มความสามารถ ข้อกำหนด หรือเอกสารใหม่ที่ยังคงความเข้ากันได้กับเวอร์ชันเดิม

### 4.3 PATCH

เพิ่มค่า PATCH เมื่อแก้ข้อผิดพลาด ปรับถ้อยคำ เพิ่มความชัดเจน หรือแก้การอ้างอิง โดยไม่เปลี่ยนความหมายเชิงบรรทัดฐาน

### 4.4 Pre-release

ใช้ส่วนต่อท้ายสำหรับเวอร์ชันที่ยังไม่ Stable เช่น:

- `draft`
- `alpha.N`
- `beta.N`
- `rc.N`

ลำดับความพร้อม:

```text
draft → alpha → beta → rc → stable
```

## 5. Version Requirements

### REQ-VER-0001 — Valid version

ทุกชุดเผยแพร่ **MUST** มี Version Identifier ที่เป็นไปตามรูปแบบในมาตรฐานนี้

### REQ-VER-0002 — Immutable release

เวอร์ชันที่เผยแพร่แล้ว **MUST NOT** ถูกเขียนทับหรือแก้ไขแบบไม่มีเวอร์ชันใหม่

### REQ-VER-0003 — Preserved history

ทุกเวอร์ชัน **MUST** ถูกเก็บไว้ใน Git history และ Snapshot ที่เกี่ยวข้องตามนโยบาย Repository

### REQ-VER-0004 — Change classification

ทุกการเผยแพร่ **MUST** ระบุว่าเป็น MAJOR, MINOR, PATCH หรือ Pre-release

### REQ-VER-0005 — Changelog

ทุกเวอร์ชันที่เผยแพร่ **MUST** มีรายการเปลี่ยนแปลงใน `CHANGELOG.md`

### REQ-VER-0006 — Migration information

การเปลี่ยนแปลงแบบ MAJOR **MUST** มี Migration Guide หรือคำอธิบายผลกระทบที่เพียงพอ

### REQ-VER-0007 — Compatibility statement

Contract ที่มีผู้ใช้งานภายนอก **MUST** ระบุ Compatibility Policy อย่างชัดเจน

### REQ-VER-0008 — Document metadata

เอกสารทุกฉบับ **MUST** ระบุเวอร์ชันของตนใน Metadata

### REQ-VER-0009 — Unique tag

Git tag สำหรับ Release **MUST** เป็นเอกลักษณ์และ **MUST NOT** ถูกย้ายไปชี้ Commit อื่นหลังเผยแพร่

### REQ-VER-0010 — Source alignment

Snapshot, tag, changelog และ release notes ของเวอร์ชันเดียวกัน **MUST** อ้างอิงเนื้อหาชุดเดียวกัน

## 6. Framework Version vs Document Version

ANEF แยกเวอร์ชันสองระดับ:

1. **Framework Version** — เวอร์ชันของชุดมาตรฐานทั้งหมด เช่น `v1.0.0-draft`
2. **Document Version** — เวอร์ชันของเอกสารรายฉบับ

Document Version **MAY** เปลี่ยนเร็วกว่าหรือช้ากว่า Framework Version แต่เอกสารที่รวมใน Snapshot **MUST** ระบุ Framework Version ที่เอกสารนั้นถูกรวมอยู่

ตัวอย่าง Metadata:

```yaml
document_id: ANEF-010
document_version: 1.0.0-draft
framework_version: 1.0.0-draft
status: Draft
```

## 7. Snapshot Policy

Repository ใช้โครงสร้าง:

```text
versions/
├── v1.0.0-draft/
├── v1.0.0/
├── v1.1.0/
└── v2.0.0/
```

กฎ:

- Snapshot ที่เผยแพร่แล้ว **MUST** ถือเป็น Immutable
- การแก้ไข Stable Snapshot **MUST** ทำผ่านเวอร์ชัน PATCH หรือเวอร์ชันใหม่
- `current/` **MAY** ชี้ไปยังเวอร์ชันที่กำลังพัฒนา แต่ **MUST NOT** ถูกใช้แทน Snapshot ถาวร
- ชื่อโฟลเดอร์ **MUST** ตรงกับ Framework Version

## 8. Document Status and Version Relationship

| Status | Version examples | Meaning |
|---|---|---|
| Proposed | `0.1.0-draft` | แนวคิดที่เสนอ ยังไม่ยอมรับเป็นมาตรฐาน |
| Draft | `1.0.0-draft` | อยู่ระหว่างการเขียนและทบทวน |
| Review | `1.0.0-rc.1` | พร้อมสำหรับการตรวจรับขั้นสุดท้าย |
| Approved | `1.0.0` | ได้รับอนุมัติและใช้อ้างอิงได้ |
| Deprecated | เวอร์ชันเดิมคงอยู่ | ยังรองรับชั่วคราว แต่มีตัวแทนใหม่ |
| Archived | เวอร์ชันเดิมคงอยู่ | ไม่พัฒนาต่อและไม่แนะนำให้เริ่มใช้งานใหม่ |

สถานะ **MUST NOT** ใช้แทน Version Identifier และ Version Identifier **MUST NOT** ใช้แทนสถานะเอกสาร

## 9. Compatibility Rules

### 9.1 Backward Compatibility

การเปลี่ยนแปลงถือว่า Backward Compatible เมื่อผู้ใช้งานเวอร์ชันก่อนสามารถทำงานต่อได้โดยไม่ต้องเปลี่ยน Contract ที่ใช้อยู่

### 9.2 Breaking Change

ตัวอย่าง Breaking Change:

- ลบ Requirement ที่ผู้ใช้งานต้องอ้างอิง
- เปลี่ยนความหมายของคำศัพท์เดิม
- ลบหรือเปลี่ยนชื่อฟิลด์บังคับของ Contract
- เปลี่ยนรูปแบบ Identifier โดยไม่มีช่วงเปลี่ยนผ่าน
- ยกเลิก API หรือ Event โดยไม่มี Compatibility Window

Breaking Change **MUST** เพิ่ม MAJOR Version เว้นแต่ Contract นั้นยังอยู่ใน Pre-release ที่ระบุชัดว่าไม่รับประกัน Compatibility

### 9.3 Additive Change

การเพิ่มเอกสาร คำศัพท์ หรือฟิลด์ Optional โดยไม่กระทบผู้ใช้งานเดิม **SHOULD** เพิ่ม MINOR Version

### 9.4 Editorial Change

การแก้คำผิด ลิงก์ หรือรูปแบบที่ไม่เปลี่ยนความหมายเชิงบรรทัดฐาน **SHOULD** เพิ่ม PATCH Version

## 10. Deprecation Policy

สิ่งที่จะยกเลิก **MUST** ผ่านขั้นตอน:

```text
Active → Deprecated → Removed
```

ข้อกำหนด:

- ต้องระบุเวอร์ชันที่เริ่ม Deprecated
- ต้องระบุสิ่งที่ใช้แทนหรือเหตุผลที่ไม่มีตัวแทน
- ต้องกำหนด Compatibility Window
- การ Removed โดยทั่วไปต้องเกิดใน MAJOR Version ถัดไป
- ประวัติเดิมต้องยังค้นหาได้

## 11. Branch and Tag Conventions

ตัวอย่างสาขา:

```text
main
release/v1.0.0
feature/anef-010-versioning
fix/anef-009-metadata
```

ตัวอย่าง tag:

```text
v1.0.0-draft
v1.0.0-rc.1
v1.0.0
v1.1.0
```

Tag **SHOULD** มี prefix `v` สำหรับ Framework Release เพื่อแยกจาก Document ID และเลขอื่น

## 12. Release Procedure

การเผยแพร่เวอร์ชัน **SHOULD** ดำเนินการตามลำดับ:

1. กำหนด Version และ Scope
2. ตรวจสอบเอกสารและ Cross References
3. ตรวจสอบ Requirement IDs และ Metadata
4. ปิดรายการ Breaking Changes
5. อัปเดต `CHANGELOG.md`
6. สร้างหรือยืนยัน Snapshot
7. สร้าง Git tag
8. เผยแพร่ Release Notes
9. ตรวจสอบลิงก์และ Artifact หลังเผยแพร่

## 13. Release Notes Requirements

Release Notes **MUST** ระบุอย่างน้อย:

- Version
- Release date
- Status
- Added
- Changed
- Deprecated
- Removed
- Fixed
- Security (ถ้ามี)
- Migration instructions (เมื่อจำเป็น)

## 14. Anti-Patterns

ห้ามหรือไม่แนะนำแนวทางต่อไปนี้:

- ใช้ชื่อ `final`, `final2`, `latest-final` แทน Version
- แก้ Release เดิมโดยไม่เพิ่ม Version
- ใช้วันที่อย่างเดียวแทน Version โดยไม่มีนโยบายกำกับ
- เปลี่ยน Contract แต่ประกาศเป็น PATCH
- ลบ Snapshot เก่าเพื่อลดจำนวนไฟล์
- ย้าย Git tag หลังเผยแพร่
- ไม่อัปเดต Changelog

## 15. Compliance Checklist

- [ ] Version เป็นไปตามรูปแบบที่กำหนด
- [ ] ระดับ MAJOR/MINOR/PATCH ถูกต้องตามผลกระทบ
- [ ] Metadata ของเอกสารครบถ้วน
- [ ] Changelog อัปเดตแล้ว
- [ ] Breaking Changes ถูกระบุแล้ว
- [ ] Migration Guide มีเมื่อจำเป็น
- [ ] Snapshot และ tag สอดคล้องกัน
- [ ] Release เดิมไม่ถูกเขียนทับ
- [ ] Deprecated items ระบุตัวแทนและช่วงเวลาแล้ว
- [ ] Cross References ตรวจสอบแล้ว

## 16. Examples

### Example A — Patch

```text
1.0.0 → 1.0.1
```

แก้คำผิดและลิงก์โดยไม่เปลี่ยน Requirement

### Example B — Minor

```text
1.0.0 → 1.1.0
```

เพิ่ม Specification ใหม่ที่ไม่ทำลายเอกสารเดิม

### Example C — Major

```text
1.4.2 → 2.0.0
```

เปลี่ยน Document ID Policy และ Contract ที่ต้อง Migration

### Example D — Pre-release

```text
2.0.0-draft → 2.0.0-beta.1 → 2.0.0-rc.1 → 2.0.0
```

## 17. Cross References

- ANEF-005 — Constitution
- ANEF-007 — Enterprise Glossary
- ANEF-008 — Naming Standard
- ANEF-009 — Documentation Standard
- ANEF-011 — Repository Structure
- ANEF-012 — Document Lifecycle
- ANEF-015 — Change Management

## 18. Revision History

| Version | Status | Description |
|---|---|---|
| 1.0.0-draft | Draft | Initial versioning standard |
