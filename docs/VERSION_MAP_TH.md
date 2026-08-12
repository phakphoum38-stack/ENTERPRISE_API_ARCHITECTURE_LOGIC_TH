# Research OS — Version Map (TH)

เอกสารนี้เป็น source of truth สำหรับการแยกสายเวอร์ชันและลด PR/implementation ที่ซ้ำกัน

## 1. Current / Main

`main` คือสายใช้งานปัจจุบันและเป็น canonical owner ของ shared infrastructure เช่น:

- lean/manual GitHub Actions policy
- canonical Candidate workflow
- Browser Use Cloud smoke workflow
- File Audit v6^6 gate
- shared Flutter/API/ServiceHost/installer infrastructure ที่ถูก merge แล้ว

ห้ามสร้าง workflow หรือ subsystem ซ้ำใน feature branch ถ้ามี canonical owner อยู่บน `main` แล้ว

## 2. V3 Next — canonical PR #25

PR #25 (`architecture/v3-clean`) เป็นสาย V3 หลักเพียงสายเดียวสำหรับงาน V3 รุ่นถัดไป

ครอบคลุม:

- Unified Master / Adaptive Brain 1^3, 3^3, 6^3, 6^6
- provider execution
- local service + Windows ServiceHost
- Flutter desktop
- Software Factory execution
- one installer + exact-SHA Candidate

PR/branch V3 รุ่นทดลองก่อนหน้าให้ถือเป็น migration/reference history และไม่ควร merge ซ้ำอีก

## 3. Owner Special — canonical PR #26

PR #26 (`copilot/fix-owner-installer-upgrade-check`) เป็นสายเฉพาะ Owner Special

- แยก lifecycle/service/installer จาก Research OS V3 ปกติ
- รักษา installer-owned upgrade quiescing
- ไม่ดึง Owner Special implementation มาปะปนกับ V3 canonical โดยตรง

## 4. Browser / Local Access / Artifact Integration — canonical PR #28

PR #28 (`agent/local-research-os-access-41f17ac`) เป็น integration owner ของ:

- Browser Use Cloud connector
- Browser Use real-cloud/simulator smoke
- local Google Workspace acceptance/access
- Website / Windows / unsigned iOS artifact build

PR #27 เป็น subset/duplicate ของสายนี้และไม่ควร merge แยก

## 5. Superseded PRs

PR ต่อไปนี้ให้ถือเป็น `superseded` และปิดโดยไม่ merge เพื่อรักษา history แต่ไม่สร้าง implementation ซ้ำ:

- #18 — AI Gateway v2 hardening prototype; superseded by later Brain/V3 provider architecture
- #19 — V2 Brain Core phases; superseded by consolidated V3 architecture
- #20 — Adaptive Software Factory V1-V2; superseded by V3 canonical Software Factory execution
- #21 — V3 AI Workspace feature map; absorbed by canonical V3 line
- #22 — Adaptive 6^6 Compound Brain; superseded by canonical V3 clean line
- #23 — Unified Master V3 integration; superseded by canonical V3 clean line
- #27 — Local access subset; superseded by PR #28

## 6. Version naming policy

ใช้ชื่อรุ่นแบบนี้เพื่อลดความสับสน:

- `Current` — สิ่งที่ merge อยู่บน `main`
- `V3 Next` — PR #25 จนกว่าจะได้รับการรับรองและ merge
- `Owner Special` — PR #26
- `Integration` — PR #28

เมื่อ V3 Next ผ่าน Candidate และ merge แล้ว ให้เปลี่ยนสถานะเป็น `Current V3` และปิดสาย V2/V3 ทดลองที่เหลือทั้งหมด

## 7. Duplication policy

ก่อนเพิ่มไฟล์/ระบบใหม่ ให้ใช้ลำดับ:

**Reuse → Update → Replace → Create**

ห้ามสร้างของซ้ำเมื่อมี canonical owner แล้ว เช่น:

- workflow ชื่อใหม่ที่ทำหน้าที่เดียวกับ workflow เดิม
- API/provider/service owner ชุดที่สอง
- installer หลายสายสำหรับ product identity เดียวกัน
- file copy เช่น `*_new`, `*_copy`, `*_final2`
- PR ที่มี subset เดียวกับ canonical integration PR

ปิด PR ที่ถูก supersede แทนการ merge ซ้ำ และเก็บ history ไว้เพื่อ audit/migration เท่านั้น
