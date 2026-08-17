# Docs Validation Generate Tool

Status: CANONICAL

## Purpose
ใช้เอกสารใน repository เป็น evidence/reference เพื่อตรวจความถูกต้องของ Timeline, workflow, dependency, artifact lineage และผลก่อน Generate หรือ Cleanup

## Rule
Docs เป็นตัวช่วยตรวจสอบ ไม่ใช่หลักฐานแทนผลจาก workflow จริง

## Flow
Timeline → Repository Docs → Workflow Definition → Dependency → Generate/Build → Validation → Artifact Lineage → Final Evidence

## Verification Gates
1. ตรวจ docs ที่เกี่ยวข้องก่อน Generate
2. ตรวจ workflow definition ให้ตรงกับ docs
3. ตรวจ dependency และ artifact lineage
4. ถ้าข้อมูลขัดกัน ให้หยุดและตรวจเพิ่ม ห้ามเดา
5. Generate เฉพาะเมื่อ docs + workflow evidence สนับสนุนว่าจำเป็น
6. ก่อนลบต้องผ่าน Pre-delete Verification Gate
7. หลัง Cleanup ตรวจ docs/lineage อีกครั้ง
8. Final valid แล้ว STOP

## GitHub Documentation Sources
- Repository files and workflow definitions
- GitHub Actions workflow runs and job evidence
- Commit history and commit SHA
- Pull request diff/review evidence

## Generate Policy
Docs สามารถใช้เป็นตัวช่วยสร้าง/ตรวจ checklist หรือ validation context ได้ แต่ห้ามใช้ docs เพียงอย่างเดียวเป็นเหตุผลให้สร้าง Build/Artifact ใหม่

## Change Policy
เพิ่มหรือแก้ docs เมื่อพบหลักฐานใหม่จาก repository/workflow จริง และต้องรักษา Source of Truth เดียวกันกับ Generate Timeline Tool
