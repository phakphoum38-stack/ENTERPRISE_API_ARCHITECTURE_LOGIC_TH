# Research OS — Version Map (TH)

เอกสารนี้เป็น source of truth สำหรับการแยกสายเวอร์ชันและลด PR/implementation ที่ซ้ำกัน

## Current / Main

`main` คือสายใช้งานปัจจุบันและ canonical owner ของ shared infrastructure เช่น Candidate, CI Lite, Release, Browser Use Cloud smoke, Artifact Build, File Audit v6^6 และ shared Flutter/API/ServiceHost/installer ที่ merge แล้ว

### Canonical GitHub Actions

ให้มีเพียง 5 workflow หลักใน `main`:

1. `ci-lite.yml` — manual exact-SHA API/Flutter validation
2. `candidate.yml` — Windows release-candidate build/install/upgrade/uninstall/evidence
3. `release.yml` — exact-SHA release lineage และ explicit publication
4. `artifacts-build.yml` — Website / Windows / unsigned iOS distribution artifacts
5. `browser-use-cloud-smoke.yml` — Browser Use simulator/real-cloud integration validation

workflow split/legacy รุ่นก่อนหน้าถูกลบออกจาก `main` แล้ว เพราะความสามารถที่ยังต้องใช้ถูกย้ายเข้า canonical workflows ข้างต้น

## V3 Next — canonical PR #25

PR #25 (`architecture/v3-clean`) เป็นสาย V3 หลักเพียงสายเดียวสำหรับงาน V3 รุ่นถัดไป ครอบคลุม Unified Master / Adaptive Brain 1^3, 3^3, 6^3, 6^6, provider execution, local service + Windows ServiceHost, Flutter desktop, Software Factory execution และ one-installer exact-SHA Candidate

PR/branch V3 รุ่นทดลองก่อนหน้าให้ถือเป็น migration/reference history และไม่ควร merge ซ้ำอีก

## Owner Special — canonical PR #26

PR #26 (`copilot/fix-owner-installer-upgrade-check`) เป็นสายเฉพาะ Owner Special และคง lifecycle/service/installer แยกจาก Research OS V3 ปกติ

## Integration Clean — canonical PR #33

PR #33 (`integration/clean-browser-local-artifacts`) เป็น integration owner ของ Browser Use Cloud, local Google Workspace access และ Website / Windows / unsigned iOS artifact build โดยสร้างใหม่บน canonical `main` เพื่อไม่ให้ workflow legacy กลับมา

## Superseded PRs

ปิดโดยไม่ merge เพื่อรักษา history แต่ไม่สร้าง implementation ซ้ำ:

- #9 — split-pipeline compatibility fix; split workflows ถูก canonical Candidate/Release แทนแล้ว
- #10 — Windows branding/release artifact branch; branding/artifact capability อยู่ใน Current workflows แล้ว
- #11 — legacy Memory Engine branch; current architecture มี local memory owner แล้ว งาน UX ที่ยังต้องการให้เพิ่มเป็น increment ใหม่แทนการ merge branch เก่า
- #18 — AI Gateway v2 hardening prototype
- #19 — V2 Brain Core phases
- #20 — Adaptive Software Factory V1-V2
- #21 — V3 AI Workspace feature map
- #22 — Adaptive 6^6 Compound Brain
- #23 — Unified Master V3 integration
- #27 — Local access subset
- #28 — Integration branch เดิม; superseded by clean PR #33
- #32 — failed/conflicted sync attempt for Integration; superseded by clean PR #33

ทั้งหมดข้างต้นถูกปิดโดยไม่ merge และ commit/history ยังอยู่สำหรับ audit หรือ migration reference

## Version naming policy

- `Current` — สิ่งที่ merge อยู่บน `main`
- `V3 Next` — PR #25 จนกว่าจะได้รับการรับรองและ merge
- `Owner Special` — PR #26
- `Integration Clean` — PR #33

เมื่อ V3 Next ผ่าน Candidate ของ SHA ล่าสุดและ merge แล้ว ให้เปลี่ยนสถานะเป็น `Current V3`

## Duplication policy

ใช้ลำดับ **Reuse → Update → Replace → Create**

ห้ามสร้าง workflow, API/provider/service owner, installer หรือ PR subset ซ้ำเมื่อมี canonical owner แล้ว ปิด PR ที่ถูก supersede แทนการ merge ซ้ำ และเก็บ history ไว้เพื่อ audit/migration เท่านั้น
