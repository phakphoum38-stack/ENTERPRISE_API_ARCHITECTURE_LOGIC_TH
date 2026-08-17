# Generate Timeline Tool

Status: CANONICAL

## Purpose
ควบคุมลำดับ Generate/Build/Validation/Final เพื่อลด workflow ซ้ำและ artifact ซ้ำ

## Canonical workflow
`.github/workflows/owner-special-friend.yml`

## Pipeline
Source → Commit SHA → Canonical Workflow → Build → Validation → Bundle → Final → SHA256/Evidence → STOP

## Rules
1. ตรวจ Final และ artifact ที่มีอยู่ก่อน Generate ทุกครั้ง
2. ถ้า Final ยัง valid: STOP และห้าม Generate ซ้ำ
3. ถ้า workflow ทำหน้าที่ซ้ำ: ใช้ canonical workflow เดิม
4. ถ้าเป็นขั้นใหม่จริง: เติมต่อท้าย Timeline ก่อนสร้าง workflow
5. ถ้า artifact หมดอายุ: Generate เฉพาะ artifact ที่หมดอายุ/หายไป
6. ห้าม rerun ทั้งสายเพียงเพราะ artifact กลางหมดอายุ
7. Final ต้องมี lineage ย้อนกลับถึง source commit และ validation evidence
8. Cleanup ทำหลัง dependency ของ artifact กลางหลุดแล้วเท่านั้น
9. Final artifact ที่ใช้งานได้ให้เหลือ 1 ผลต่อ target

## Pre-delete verification gate
ก่อนลบ workflow, artifact หรือผล Build ใด ๆ ต้องตรวจให้ครบ:

1. ไม่มี workflow อื่นเรียกหรืออ้างอิงอยู่
2. ไม่เป็น dependency ของขั้นตอนถัดไป
3. ไม่ใช่ Final artifact ที่ยัง valid
4. ไม่ใช่ SHA256/Evidence ที่ต้องเก็บ
5. ไม่มี PR หรือ branch ที่ยังอ้างอิง
6. ไม่มี workflow run ที่ต้องใช้ผลนั้นต่อ
7. สามารถย้อน lineage ไปยัง source commit และ validation ได้

ถ้าตรวจข้อใดไม่ได้หรือมีความไม่แน่นอน → **ห้ามลบ** และเก็บไว้ตรวจต่อ

## Cleanup policy
- ลบเฉพาะตัวที่ผ่าน Pre-delete verification ครบทุกข้อ
- ลบเป็นรอบเดียวหลัง Audit เสร็จ
- หลัง Cleanup ต้องตรวจซ้ำว่า Canonical pipeline ยังทำงานได้
- ห้าม Generate ใหม่เพื่อทดแทนของที่ลบ จนกว่า Final Gate จะยืนยันว่าจำเป็น

## Timeline
T0 Foundation
T1 Owner/Friend Master
T2 V3 Bridge
T3 Desktop Build
T4 Installer Build
T5 Installer Validation
T6 Owner Bundle
T7 Final Release
T8 SHA256 + Evidence
T9 Pre-delete Verification
T10 Cleanup
T11 Final Gate
T12 STOP

## Change policy
ห้ามสร้าง Generate workflow ใหม่จากการคาดเดา หากยังไม่มีหลักฐานว่า workflow เดิมไม่รองรับขั้นตอนนั้น
