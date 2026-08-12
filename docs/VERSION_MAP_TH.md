# Research OS — Version Map (TH)

เอกสารนี้เป็น source of truth สำหรับการแยกสายเวอร์ชันและลด PR/implementation ที่ซ้ำกัน

## Current / Main

`main` คือสายใช้งานปัจจุบันและ canonical owner ของ shared infrastructure เช่น lean/manual GitHub Actions, Candidate workflow, Browser Use Cloud smoke, File Audit v6^6 และ shared Flutter/API/ServiceHost/installer ที่ merge แล้ว

## V3 Next — canonical PR #25

PR #25 (`architecture/v3-clean`) เป็นสาย V3 หลักเพียงสายเดียวสำหรับงาน V3 รุ่นถัดไป ครอบคลุม Unified Master / Adaptive Brain 1^3, 3^3, 6^3, 6^6, provider execution, local service + Windows ServiceHost, Flutter desktop, Software Factory execution และ one-installer exact-SHA Candidate

PR/branch V3 รุ่นทดลองก่อนหน้าให้ถือเป็น migration/reference history และไม่ควร merge ซ้ำอีก

## Owner Special — canonical PR #26

PR #26 (`copilot/fix-owner-installer-upgrade-check`) เป็นสายเฉพาะ Owner Special และคง lifecycle/service/installer แยกจาก Research OS V3 ปกติ

## Integration — canonical PR #28

PR #28 (`agent/local-research-os-access-41f17ac`) เป็น integration owner ของ Browser Use Cloud, local Google Workspace access และ Website / Windows / unsigned iOS artifact build

PR #27 เป็น subset/duplicate ของสายนี้และไม่ควร merge แยก

## Superseded PRs

ปิดโดยไม่ merge เพื่อรักษา history แต่ไม่สร้าง implementation ซ้ำ:

- #18 — AI Gateway v2 hardening prototype
- #19 — V2 Brain Core phases
- #20 — Adaptive Software Factory V1-V2
- #21 — V3 AI Workspace feature map
- #22 — Adaptive 6^6 Compound Brain
- #23 — Unified Master V3 integration
- #27 — Local access subset

## Version naming policy

- `Current` — สิ่งที่ merge อยู่บน `main`
- `V3 Next` — PR #25 จนกว่าจะได้รับการรับรองและ merge
- `Owner Special` — PR #26
- `Integration` — PR #28

เมื่อ V3 Next ผ่าน Candidate และ merge แล้ว ให้เปลี่ยนสถานะเป็น `Current V3`

## Duplication policy

ใช้ลำดับ **Reuse → Update → Replace → Create**

ห้ามสร้าง workflow, API/provider/service owner, installer หรือ PR subset ซ้ำเมื่อมี canonical owner แล้ว ปิด PR ที่ถูก supersede แทนการ merge ซ้ำ และเก็บ history ไว้เพื่อ audit/migration เท่านั้น
