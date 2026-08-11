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

## โครงสร้าง GitHub Actions ปัจจุบัน

ใช้ workflow หลัก/เฉพาะทางทั้งหมด 5 ตัว และทุกตัวเป็น **manual-only**:

1. `ci-lite.yml`
   - ตรวจ Python/API ตาม exact SHA
   - Flutter analyze/test เปิดเพิ่มได้ตามต้องการ
   - ไม่รันอัตโนมัติทุก push หรือ pull request

2. `candidate.yml`
   - canonical owner ของ Windows release-candidate validation
   - Windows runner เพียง 1 ตัว
   - Build/Test Windows App
   - Build/Test ServiceHost และ Runtime
   - Build Setup EXE
   - Install + In-place Upgrade + Uninstall
   - ตรวจการเก็บข้อมูลเดิม
   - ตรวจ loopback-only และ secret-safe provider status
   - สร้าง exact-SHA manifest + SHA256
   - Upload verified candidate artifact

3. `release.yml`
   - รับ candidate run ID และ exact SHA
   - ตรวจ lineage + SHA256 ก่อน
   - ไม่สร้าง Release โดยค่าเริ่มต้น
   - สร้าง GitHub Release เฉพาะเมื่อ `publish=true`

4. `artifacts-build.yml`
   - สร้าง distribution/developer artifacts แบบเลือกได้สำหรับ Website, Windows และ unsigned iOS IPA
   - เป็น manual-only และผูกกับ exact SHA
   - artifact จาก workflow นี้ **ไม่ถือเป็น verified release candidate evidence**
   - Windows Setup จาก workflow นี้ใช้สำหรับ build/distribution validation เท่านั้น; การออก Release ต้องใช้ artifact lineage จาก `candidate.yml`

5. `browser-use-cloud-smoke.yml`
   - ตรวจ Browser Use connector/API/Flutter contract แบบ end-to-end
   - ค่าเริ่มต้นใช้ local simulator จึงไม่ใช้ Browser Use Cloud quota
   - real cloud เป็น opt-in และต้องใช้ `BROWSER_USE_API_KEY` จาก GitHub Secrets
   - ไม่เปิดเผย API key หรือ CDP URL ใน status payload

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

## CI Lite

ใช้เมื่อ local preflight ยังไม่พอและต้องการหลักฐานบน GitHub เพิ่มเติม ให้ dispatch `Research OS CI Lite` ด้วย exact SHA ที่ต้องการตรวจ

ห้ามใช้ push trigger เป็นค่าเริ่มต้น เพราะขัดกับหลัก zero-Actions-per-development-commit

## Candidate

เมื่อเขียนงานชุดนั้นเสร็จแล้ว ให้สั่ง `Research OS Candidate` เพียง 1 ครั้งจาก workflow ที่ลงทะเบียนบน `main` และระบุ exact SHA ของ branch/commit ที่ต้องการตรวจ

ห้ามเปิด Candidate หลาย run สำหรับ SHA เดียวกันโดยไม่จำเป็น

`candidate.yml` บน `main` เป็น canonical owner ของ candidate gate; feature branch ไม่ควรสร้างสำเนา workflow นี้เอง

## Distribution Artifacts

ถ้าต้องการเฉพาะไฟล์ Website, Windows หรือ unsigned iOS IPA โดยยังไม่ต้องการ candidate evidence ให้ใช้ `Research OS Artifact Build`

- ต้องระบุ exact SHA เมื่อ build งานสำคัญ
- ไม่ถือ artifact จาก workflow นี้เป็น Release Candidate โดยอัตโนมัติ
- Release lineage ต้องย้อนกลับไปยัง Candidate ที่ผ่าน validation เท่านั้น

## Browser Use Cloud Smoke

ใช้ `Browser Use Cloud Connect Smoke` เมื่อมีการแก้ connector, backend route หรือ Flutter connect UI

- ค่าเริ่มต้น `connect_cloud=false` ใช้ simulator
- เปิด `connect_cloud=true` เฉพาะเมื่อจำเป็นต้องพิสูจน์ real-cloud integration
- real-cloud secret ต้องอยู่ใน GitHub Secrets เท่านั้น

## Release

Release แยกจาก Candidate เสมอ

- Candidate ผ่าน ≠ Release
- Merge ≠ Release
- Distribution artifact ≠ Release Candidate
- Release ต้องสั่งเอง
- Production code signing ต้องเพิ่มเมื่อมี trusted certificate จริง
- ห้ามใช้ self-signed certificate เป็น production signing

## Security gates ที่ทำแล้ว

- OAuth callback request logging ต้องไม่บันทึกค่า query ที่มี `code` หรือ `state`
- HTTP handler ต้อง redact callback query เป็น `?[REDACTED]` ก่อนเขียน persistent request log
- regression test ต้องตรวจว่าค่า OAuth callback secret ไม่ปรากฏใน log
- Browser Use status ต้องไม่ส่ง API key หรือ CDP URL กลับไปยัง client

## สิ่งที่ยกเลิกจาก workflow เดิม

นำ workflow ย่อยที่เคยรันแยกกันออก เช่น Windows App, ServiceHost, Runtime Smoke, Installer Build, Installer Validation, Branding, Agent Platform, Completion Crew, Performance, Nightly, Pages, Provider Smoke, Gemini E2E, Google Workspace, Production Health และ staging/RC gates

ความสามารถที่จำเป็นต่อ Windows Candidate ถูกรวมไว้ใน canonical `candidate.yml`

งาน Browser Use และ cross-platform artifact build คงไว้เป็น manual specialized workflows เพราะมี runner/credential/lifecycle ต่างจาก Candidate โดยตรง

## หลักประหยัด Actions

- ไม่ใช้ `pull_request` auto-build
- ไม่ใช้ `push` auto-build
- ไม่ใช้ scheduled/nightly โดยค่าเริ่มต้น
- ไม่ dispatch workflow ต่อ workflow
- ไม่สร้าง intermediate artifacts หลายรอบโดยไม่จำเป็น
- ใช้ exact SHA เดียวตลอด Candidate
- ใช้ Windows runner หนึ่งตัวตลอด Candidate
- Release เป็น manual-only
- real Browser Use Cloud เป็น opt-in; simulator เป็นค่าเริ่มต้น
- การเรียกผู้ช่วย AI ปกติไม่ใช้ GitHub Actions

## หมายเหตุเรื่อง Branch Protection

ถ้า GitHub Branch Protection เคยตั้ง required checks ด้วยชื่อ workflow เก่า ต้องปรับ required checks ให้ตรงกับโครงสร้างใหม่ก่อน Merge
