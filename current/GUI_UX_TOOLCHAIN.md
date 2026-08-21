# GUI/UX Toolchain — ibisPaint + Figma + Research OS

**Document ID:** ANEF-GUI-001  
**Version:** v1.0.0-draft  
**Status:** Proposed / Integration Ready  
**Revision:** 1  

## Purpose

กำหนดเส้นทางสำหรับงาน GUI/UX ของ Research OS โดยแยกงาน visual artwork ออกจาก UI structure และ implementation และเชื่อมกลับเข้าสู่ CI/E2E/Evidence pipeline ด้วย contract ที่ชัดเจน

## Tool Roles

### ibisPaint

ใช้สำหรับสร้าง visual artwork และ asset เช่น:

- illustration
- background
- splash / onboarding artwork
- icons และ decorative assets
- character / assistant artwork
- visual concepts

ibisPaint เป็น **authoring tool** ไม่ใช่ runtime dependency ของ Research OS และไม่ควรถูกติดตั้งเป็น dependency ใน GitHub Actions

### Figma

ใช้สำหรับ:

- screen/layout composition
- components
- spacing / typography
- responsive structure
- interaction design
- design-system handoff

### Research OS / Flutter

รับผิดชอบ:

- asset integration
- UI implementation
- runtime behavior
- accessibility / responsive checks
- E2E และ visual regression

## Pipeline

```text
Design Brief
    ↓
Visual Concept
    ↓
ibisPaint Artwork
    ↓
PNG / PSD Export
    ↓
Asset Validation
    ↓
Figma UI Composition
    ↓
Flutter Implementation
    ↓
GUI Build
    ↓
E2E / Visual Regression
    ↓
Evidence
```

## Repository Layout

```text
design/
├── concepts/
├── artwork/
├── icons/
├── backgrounds/
├── exports/
│   ├── png/
│   └── psd/
└── manifest/
```

## Asset Contract

ทุก asset ที่เข้าสู่ implementation ควรมี metadata อย่างน้อย:

```yaml
id: GUI-ASSET-XXXX
source: ibispaint
format: png|psd
version: 1.0.0
status: draft|approved|deprecated
purpose: <description>
license: <record source/license information>
checksum: <sha256 when committed>
```

ห้ามสมมติว่า asset หรือ brush/resource ใด ๆ สามารถ redistribute ได้โดยไม่มีการตรวจสิทธิ์การใช้งาน

## 6^6 Orchestration

ใช้ 6 logical lanes โดยไม่สร้าง physical workers 46,656 ตัว:

1. `GUI-01` — Visual Concept
2. `GUI-02` — Artwork / Asset
3. `GUI-03` — Asset Validation
4. `GUI-04` — Figma Composition
5. `GUI-05` — Flutter Implementation
6. `GUI-06` — Visual Regression / E2E

Execution จริงต้องผ่าน queue, backpressure และ bounded workers

```text
6^6 logical capacity
        ↓
queue
        ↓
backpressure
        ↓
bounded execution
        ↓
result / evidence
```

## CI Boundary

ibisPaint และ Figma **ไม่เป็น dependency ของ CI runtime**

CI ตรวจเฉพาะผลลัพธ์ที่ commit เข้ามา เช่น:

- file existence
- supported format
- dimensions / size policy
- manifest consistency
- checksum consistency
- Flutter build
- E2E / visual regression

## Integration Rule

GUI/UX Toolchain ต้องไม่ถูกนำไปแก้หรือผูกกับ `research-os-gate` startup failure โดยตรง งาน GUI จะเชื่อมเข้าหลังจาก CI baseline และ E2E path มีหลักฐานที่เสถียรแล้ว

## Definition of Done

- [ ] Design brief มี owner และ version
- [ ] Artwork มี source/license record
- [ ] PNG/PSD ผ่าน asset validation
- [ ] Figma composition ผ่าน review
- [ ] Flutter implementation build ผ่าน
- [ ] E2E ผ่าน
- [ ] Visual regression ผ่าน หรือมี approved baseline
- [ ] Evidence ถูกบันทึก
- [ ] Asset manifest ตรงกับ repository

## Reference

Official ibisPaint website: https://ibispaint.com/?lang=th

> Design Once. Build Everywhere. Scale Forever.
