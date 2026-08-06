# ENTERPRISE API ARCHITECTURE LOGIC TH

Repository นี้เป็นแหล่งอ้างอิงหลักสำหรับเอกสาร **AI Native Enterprise Framework (ANEF)** และตรรกะสถาปัตยกรรมระดับ Enterprise ภาษาไทย

## หลักการจัดเก็บทุกเวอร์ชัน

- ทุกเวอร์ชันต้องถูกเก็บแยกไว้ใน `versions/`
- ห้ามเขียนทับหรือลบเวอร์ชันเก่าโดยไม่มีบันทึกการตัดสินใจ
- `current/` ใช้ชี้สถานะของเวอร์ชันที่กำลังพัฒนา
- ทุกเอกสารต้องมี Document ID, Version, Status และ Revision History
- ใช้ Semantic Versioning เช่น `v1.0.0-draft`, `v1.0.0`, `v1.1.0`, `v2.0.0`

## เวอร์ชันปัจจุบัน

- **Version:** `v1.0.0-draft`
- **Status:** Foundation Phase
- **Part:** Part 1 — Foundation
- **เอกสารล่าสุด:** ANEF-011 — Repository Structure

## โครงสร้าง

```text
.
├── README.md
├── CHANGELOG.md
├── VERSION_INDEX.md
├── current/
│   └── README.md
└── versions/
    └── v1.0.0-draft/
        ├── README.md
        └── docs/
            └── 00_FOUNDATION/
```

## เป้าหมาย

ANEF เป็น Framework ที่เป็นกลางต่อภาษา แพลตฟอร์ม ผู้ให้บริการ AI ระบบฐานข้อมูล และ Cloud Provider โดยใช้เอกสาร Contract และหลักฐานทางสถาปัตยกรรมเป็นแหล่งอ้างอิงหลัก

> Design Once. Build Everywhere. Scale Forever.
