# Research OS — Lean Workflow Policy (TH)

## เป้าหมาย

ลดการใช้ GitHub Actions ให้เหลือเท่าที่จำเป็น โดยยึดหลัก:

> เขียนให้เสร็จก่อน ตรวจบนเครื่องก่อน และ Build ตัวติดตั้งจริงเพียงครั้งเดียวต่อ Candidate

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

### สิ่งที่ต้องหลีกเลี่ยง

- ไม่สร้างไฟล์สำเนาเช่น `*_new`, `*_copy`, `*_final2` เพื่อเลี่ยงการแก้ไฟล์เดิม
- ไม่สร้าง API/provider/config/store/workflow ซ้ำเมื่อมี owner เดิม
- ไม่เก็บข้อมูลสถานะเดียวกันหลายแหล่งโดยไม่มีเหตุผลด้าน migration/rollback
- ไม่สร้าง test ชุดใหม่ทั้งชุดถ้าขยาย test เดิมได้
- ไม่สร้าง artifact ระหว่างทางหลายชุดโดยไม่จำเป็น
- ไม่แตก workflow ตามจำนวนผู้ช่วย AI

### ข้อมูลเดิม

- เมื่อข้อมูลเดิมแก้ไขได้ ให้ update record/source เดิมแทนการสร้าง duplicate record
- เก็บ backup เฉพาะเมื่อจำเป็นต่อ rollback, migration หรือการเปลี่ยนแปลงที่ย้อนกลับไม่ได้
- backup ไม่ใช่ source of truth ใหม่
- หลัง migration สำเร็จ ระบบต้องกลับมามี canonical owner เพียงชุดเดียว

### ผู้ช่วย AI หลายตัว

- Master Orchestrator เป็นผู้ประสานการเขียนจริง
- ผู้ช่วยสามารถวิเคราะห์/เสนอ patch พร้อมกันได้ แต่ **ห้ามเขียน path เดียวกันพร้อมกัน**
- งานที่แตะไฟล์เดียวกันต้อง serialize ผ่าน owner เดียว เพื่อลด conflict และไฟล์ซ้ำ
- จำนวนผู้ช่วย 1, 6, 6³ หรือ 6⁶ ไม่สัมพันธ์กับจำนวน GitHub workflow runs
- การเรียกผู้ช่วยใน Research OS runtime ใช้ **0 GitHub Actions runs**

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
- การเรียกผู้ช่วย AI ปกติไม่ใช้ GitHub Actions

## หมายเหตุเรื่อง Branch Protection

ถ้า GitHub Branch Protection เคยตั้ง required checks ด้วยชื่อ workflow เก่า ต้องปรับ required checks ให้ตรงกับโครงสร้างใหม่ก่อน Merge
