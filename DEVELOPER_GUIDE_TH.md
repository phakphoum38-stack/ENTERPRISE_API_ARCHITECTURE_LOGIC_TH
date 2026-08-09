# Research OS v1 — Developer / Maintainer Guide

> เอกสารนี้สำหรับ Developer, Maintainer และผู้ดูแลระบบเชิงเทคนิค
> ผู้ใช้ทั่วไปควรใช้ `INSTALLATION_AND_USAGE_TH.md`

เอกสารนี้แยกเรื่อง source code, API, service scripts, build, testing, CI/CD, release และ debugging ออกจากคู่มือผู้ใช้ทั่วไปโดยตั้งใจ

---

## 1. Source-of-truth

Repository หลัก:

```text
phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH
```

V1 ใช้หลัก Long-term First, One Truth, AI is a Team Member, Every Change Has Evidence, Documentation Never Lags Behind Code และ Quality Is Continuous

## 2. โครงสร้างส่วนสำคัญ

```text
apps/research_os_flutter/
tools/research_os_api/
tools/research_os_service/
tools/research_curator/
installer/
scripts/
.github/workflows/
research/artifacts/
```

## 3. Flutter Desktop

แอปหลักอยู่ใน:

```text
apps/research_os_flutter
```

เมนูหลักถูกประกอบใน `lib/src/app_shell.dart` และ navigation อยู่ใน `lib/src/ui/enterprise_navigation.dart`

ก่อน merge การเปลี่ยนแปลง UI ควรรัน:

```bash
flutter analyze
flutter test
```

Windows release build:

```bash
flutter build windows --release
```

## 4. Local API

API modules อยู่ใน:

```text
tools/research_os_api
```

Local API มาตรฐาน:

```text
http://127.0.0.1:8787
```

Endpoints สำคัญ:

```text
GET  /health
GET  /v1/providers
POST /v1/ai/generate
POST /v1/conversations/analyze
GET  /v1/knowledge/artifacts
GET  /v1/knowledge/graph
GET  /v1/agents/orchestrations
POST /v1/agents/orchestrations
GET  /v1/agents/orchestrations/{run_id}
POST /v1/agents/orchestrations/{run_id}/execute
POST /v1/agents/orchestrations/{run_id}/confirm
```

OpenAPI contract:

```text
tools/research_os_api/openapi.yaml
```

เมื่อเปลี่ยน endpoint ต้องอัปเดต contract และ tests พร้อมกัน

## 5. Agent Platform

โมดูลหลักประกอบด้วย agent registry/capability routing, runtime, shared context, orchestrator, dependency delegation และ confirmation policy

Developer ต้องรักษาหลักว่า write-capable action ต้องไม่ bypass permission/confirmation policy

## 6. Windows Service

Service name:

```text
ResearchOSService
```

ServiceHost:

```text
tools/research_os_service/publish/ResearchOS.ServiceHost.exe
```

Script สำหรับจัดการ service:

```text
scripts/research-os-service.ps1
```

Actions ที่รองรับ:

```text
install
uninstall
start
stop
restart
status
```

ตัวอย่าง:

```powershell
& .\scripts\research-os-service.ps1 -Action status
```

งาน install/start/stop/restart/uninstall ต้องใช้ Administrator

## 7. Environment ของ Service

Service ใช้ตัวแปรหลัก:

```text
RESEARCH_OS_REPO_ROOT
RESEARCH_OS_DATA_DIR
RESEARCH_OS_PYTHON_EXE
RESEARCH_OS_API_HOST
RESEARCH_OS_API_PORT
```

พอร์ตมาตรฐานคือ `8787`

## 8. Local Data

Installer production ใช้:

```text
C:\ProgramData\ResearchOS
```

ส่วนสำคัญ:

```text
database/
sessions/
artifacts/
backups/
logs/
```

Developer ต้องหลีกเลี่ยง migration หรือ cleanup ที่ทำลาย backward compatibility โดยไม่มี backup/rollback plan

## 9. Build ServiceHost

ServiceHost production ถูก publish สำหรับ `win-x64` แบบ self-contained เพื่อให้ผู้ใช้ทั่วไปไม่ต้องติดตั้ง .NET runtime แยก

CI จะตรวจ Python modules/API tests ก่อน upload ServiceHost artifact

## 10. Installer

Inno Setup definition:

```text
installer/research-os.iss
```

Installer package รวม:

```text
Flutter Windows app
ServiceHost
Research OS API Python modules
Research Curator
Research artifacts เมื่อมี
service scripts
bundled Python runtime
```

Developer ต้องตรวจ app version และ installer metadata ให้ตรงกันก่อน stable release

## 11. Installer Validation

ห้ามถือว่า build installer สำเร็จเท่ากับติดตั้งได้จริง ต้องผ่าน validation ที่ติดตั้ง service, ตรวจ health และถอนการติดตั้งตาม workflow ที่กำหนด

## 12. CI/CD Chain

V1 release chain หลัก:

```text
Build Windows App
        +
Build Service Host
        ↓
Runtime Smoke
        ↓
Build Installer
        ↓
Installer Validation
        ↓
Release
        ↓
Windows Compatibility Gate
        ↓
Secondary Validation
        ↓
Production Health / Pages
```

ทุก release candidate ควรผูกกับ target SHA เดียวกัน

## 13. Verified Release Artifact

Release workflow สร้าง verified installer artifact พร้อม verification manifest และ SHA-256 digest

Developer ต้องใช้ artifact ที่มาจาก successful Release run ของ candidate SHA ที่ต้องการ ไม่ควรนำไฟล์จาก local build มาปะปนกับ verified release

## 14. Production Health

Production Health ตรวจ live endpoints หลัง release และผูกกับ successful release candidate evidence

หมายเหตุ: live health ยืนยัน availability แต่หากต้องการ strict deployment provenance ควรให้ health endpoint แสดง deployed build SHA แล้ว compare กับ target SHA ในอนาคต

## 15. Testing Strategy

ก่อน promotion ต้องมีหลักฐานอย่างน้อย:

```text
flutter analyze
Flutter unit/widget tests
Agent Platform tests
API tests
Windows release build
Runtime smoke
Installer validation
Release artifact
Production Health
```

## 16. Provider Tests

Standard CI ไม่ควรถูกผูกกับ live external provider แบบบังคับ เพราะ network/key/provider availability ทำให้ CI ไม่ deterministic

ใช้ mock provider สำหรับ normal CI และแยก live provider smoke เป็น manual/explicit validation

## 17. GitHub / Google Workspace Integration

Developer ต้องแยก read และ write capability ให้ชัดเจน และรักษา confirmation policy สำหรับการเปลี่ยนข้อมูล

Credentials/secrets ต้องอยู่ในระบบ secrets/connection ที่เหมาะสม ไม่ hard-code ลง repository

## 18. Version Promotion

แนวทาง V1:

```text
0.9.0-dev.1
→ 0.9.0-rc.1
→ 1.0.0
```

การ bump version เปลี่ยน SHA ดังนั้น stable promotion ต้องผ่าน CI ของ versioned commit เอง ไม่ควรอ้างเฉพาะ SHA ก่อน bump โดยไม่ตรวจ promotion PR

## 19. Rollback / Baseline

ก่อน stable release ต้องบันทึก baseline candidate SHA และ verified release artifact digest เพื่อให้ย้อนกลับได้

Rollback ควรย้อนทั้ง code reference และ artifact ที่ตรวจสอบแล้ว ไม่ใช่ rebuild จาก source แบบไม่มีหลักฐาน

## 20. Debugging

ลำดับตรวจปัญหาที่แนะนำ:

1. ตรวจ CI/job ที่ล้มก่อน
2. ตรวจ Service status
3. ตรวจ port 8787
4. ตรวจ `/health`
5. ตรวจ logs ใน `ProgramData\ResearchOS\logs`
6. ตรวจ provider status
7. ตรวจ orchestration/agent runtime เฉพาะเมื่อ backend health ปกติ

อย่าแก้ workflow ที่เขียวอยู่เพียงเพื่อทดลอง หาก failure ชี้ว่า workflow ไม่ใช่ต้นเหตุ

## 21. Separation Policy

ผู้ใช้ทั่วไปไม่ควรต้องเห็นหรือทำงานกับ:

```text
source checkout
Flutter SDK
.NET SDK
Python development runtime
service registration commands
OpenAPI editing
GitHub Actions internals
build artifacts resolution
release run IDs
CI debugging
```

สิ่งเหล่านี้เป็น Developer/Maintainer surface และต้องแยกจาก installer + UI ของผู้ใช้ทั่วไป

## 22. เอกสารที่เกี่ยวข้อง

- `INSTALLATION_AND_USAGE_TH.md` — คู่มือผู้ใช้ทั่วไป
- `SYSTEM_OVERVIEW_TH.md` — ภาพรวมทุก subsystem
- `V1_FAST_TRACK.md` — release gates/evidence
- `V2_FAST_TRACK.md` — V2 roadmap เมื่อเริ่มพัฒนา

หลักสำคัญคือ **ผู้ใช้ติดตั้งและใช้งานได้โดยไม่ต้องเป็น Developer** ขณะที่ Developer ยังเข้าถึง source, architecture, tests และ release system ได้ครบโดยไม่ลดความสามารถของโครงการ
