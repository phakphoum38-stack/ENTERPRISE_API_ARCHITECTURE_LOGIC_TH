# Research OS — Lean Workflow Policy (TH)

## เป้าหมาย

ลดการใช้ GitHub Actions ให้เหลือเท่าที่จำเป็น โดยยึดหลัก:

> เขียนให้เสร็จก่อน ตรวจบนเครื่องก่อน และสั่ง GitHub Actions เฉพาะเมื่อมีเหตุผลชัดเจน

พร้อมใช้กฎการเปลี่ยนแปลงหลักของโปรเจกต์:

> **Reuse → Update → Replace → Create**
>
> ใช้ของเดิมก่อน แก้ของเดิมให้เป็นข้อมูลล่าสุดก่อน การสร้างของใหม่เป็นทางเลือกสุดท้าย

## กฎ Reuse → Update → Replace → Create

ก่อนแก้ทุกงาน ผู้ช่วย/นักพัฒนาต้องตรวจว่ามี owner, ไฟล์, config, endpoint, test, workflow หรือข้อมูลเดิมที่ทำหน้าที่นั้นอยู่แล้วหรือไม่

ลำดับบังคับ:

1. **Reuse** — ใช้ owner และโครงสร้างเดิม ถ้ายังรองรับงานได้
2. **Update** — แก้ข้อมูล/โค้ด/ค่ากำหนดเดิมให้เป็นสถานะล่าสุด
3. **Replace** — เปลี่ยน implementation เดิมเมื่อจำเป็น โดยรักษา contract, migration และ rollback ที่ต้องใช้
4. **Create** — สร้างใหม่เฉพาะเมื่อไม่มี canonical owner เดิมจริง ๆ หรือของเดิมไม่สามารถขยายได้อย่างปลอดภัย

## โครงสร้าง GitHub Actions ปัจจุบัน

ใช้ workflow หลัก/เฉพาะทางทั้งหมด 5 ตัว และทุกตัวเป็น **manual-only**:

1. `ci-lite.yml`
2. `candidate.yml`
3. `release.yml`
4. `artifacts-build.yml`
5. `browser-use-cloud-smoke.yml`

ระหว่างพัฒนาใช้ local preflight เป็นหลัก และใช้ exact SHA เมื่อ dispatch CI/Candidate/Artifact Build. Candidate ผ่าน ≠ Release, Merge ≠ Release, Distribution artifact ≠ Release Candidate.

## หลักประหยัด Actions

- ไม่ใช้ `pull_request` auto-build
- ไม่ใช้ `push` auto-build
- ไม่ใช้ scheduled/nightly โดยค่าเริ่มต้น
- ไม่ dispatch workflow ต่อ workflow
- ไม่สร้าง intermediate artifacts หลายรอบโดยไม่จำเป็น
- ใช้ exact SHA เดียวตลอด Candidate
- Release เป็น manual-only
- real Browser Use Cloud เป็น opt-in; simulator เป็นค่าเริ่มต้น

## หมายเหตุเรื่อง Branch Protection

ถ้า GitHub Branch Protection เคยตั้ง required checks ด้วยชื่อ workflow เก่า ต้องปรับ required checks ให้ตรงกับโครงสร้างใหม่ก่อน Merge
