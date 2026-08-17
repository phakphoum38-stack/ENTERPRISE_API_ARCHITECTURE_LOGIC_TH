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
T9 Cleanup
T10 STOP

## Change policy
ห้ามสร้าง Generate workflow ใหม่จากการคาดเดา หากยังไม่มีหลักฐานว่า workflow เดิมไม่รองรับขั้นตอนนั้น
