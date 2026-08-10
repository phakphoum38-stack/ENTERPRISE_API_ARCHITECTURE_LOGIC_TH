# Research OS — Lean Workflow Policy (TH)

## เป้าหมาย

ลดการใช้ GitHub Actions ให้เหลือเท่าที่จำเป็น โดยยึดหลัก:

> เขียนให้เสร็จก่อน ตรวจบนเครื่องก่อน และ Build ตัวติดตั้งจริงเพียงครั้งเดียวต่อ Candidate

## โครงสร้างใหม่

เหลือ GitHub Actions เพียง 3 workflow:

1. `ci-lite.yml`
   - Manual only
   - ใช้เมื่อต้องการตรวจบน GitHub เพิ่มเติม
   - ค่าเริ่มต้นตรวจ Python/API
   - Flutter check เปิดเพิ่มได้ตามต้องการ

2. `candidate.yml`
   - Manual only
   - Windows runner เพียง 1 ตัว
   - Build/Test Windows App
   - Build/Test ServiceHost และ Runtime
   - Build Setup EXE เพียงครั้งเดียว
   - Install + In-place Upgrade + Uninstall
   - ตรวจการเก็บข้อมูลเดิม
   - ตรวจ loopback-only และ secret-safe provider status
   - สร้าง exact-SHA manifest + SHA256
   - Upload verified candidate artifact

3. `release.yml`
   - Manual only
   - รับ candidate run ID และ exact SHA
   - ตรวจ lineage + SHA256 ก่อน
   - ไม่สร้าง Release โดยค่าเริ่มต้น
   - สร้าง GitHub Release เฉพาะเมื่อ `publish=true`

## ระหว่างพัฒนา

ใช้:

```powershell
.\scripts\research-os-preflight.ps1
```

GitHub Actions = 0 นาทีต่อ commit ถ้าไม่สั่ง workflow เอง

สามารถข้าม Flutter ชั่วคราวได้:

```powershell
.\scripts\research-os-preflight.ps1 -SkipFlutter
```

หรือข้าม ServiceHost build:

```powershell
.\scripts\research-os-preflight.ps1 -SkipServiceHost
```

## Candidate

เมื่อเขียนงานชุดนั้นเสร็จแล้ว ให้สั่ง `Research OS Candidate` เพียง 1 ครั้ง และระบุ SHA ที่ต้องการตรวจ

ห้ามเปิด Candidate หลาย run สำหรับ SHA เดียวกันโดยไม่จำเป็น

## Release

Release แยกจาก Candidate เสมอ

- Candidate ผ่าน ≠ Release
- Merge ≠ Release
- Release ต้องสั่งเอง
- Production code signing ต้องเพิ่มเมื่อมี trusted certificate จริง
- ห้ามใช้ self-signed certificate เป็น production signing

## สิ่งที่ยกเลิกจาก workflow เดิม

นำ workflow ย่อยที่เคยรันแยกกันออก เช่น Windows App, ServiceHost, Runtime Smoke, Installer Build, Installer Validation, Branding, Agent Platform, Completion Crew, Performance, Nightly, Pages, Provider Smoke, Gemini E2E, Google Workspace, Production Health และ staging/RC gates

ความสามารถที่จำเป็นต่อ Windows Candidate ถูกรวมไว้ใน `candidate.yml`

งานเฉพาะทางที่ไม่จำเป็นต่อ Candidate ให้รันแบบ local/manual ตามความต้องการแทน

## หลักประหยัด Actions

- ไม่ใช้ `pull_request` auto-build
- ไม่ใช้ `push` auto-build
- ไม่ใช้ scheduled/nightly โดยค่าเริ่มต้น
- ไม่ dispatch workflow ต่อ workflow
- ไม่สร้าง intermediate artifacts หลายรอบ
- ใช้ exact SHA เดียวตลอด Candidate
- ใช้ Windows runner หนึ่งตัวตลอด Candidate
- Release เป็น manual-only

## หมายเหตุเรื่อง Branch Protection

ถ้า GitHub Branch Protection เคยตั้ง required checks ด้วยชื่อ workflow เก่า ต้องปรับ required checks ให้ตรงกับโครงสร้างใหม่ก่อน Merge
