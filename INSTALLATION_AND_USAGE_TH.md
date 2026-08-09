# Research OS v1 — คู่มือการติดตั้งและการใช้งาน

เอกสารนี้อธิบายวิธีติดตั้งและใช้งาน Research OS v1 บน Windows สำหรับผู้ใช้ทั่วไปและผู้ดูแลระบบ รวมถึงการตรวจสอบ Local API, Windows Service, Agent Center และการถอนการติดตั้ง

> สถานะเอกสาร: V1 User Guide
> เป้าหมายเวอร์ชันแอป: 1.0.0
> แพลตฟอร์มหลัก: Windows x64

---

## 1. ภาพรวม Research OS

Research OS เป็น Enterprise Workspace แบบ local-first ที่รวม UI, Local API, Windows Service, Memory/Knowledge, Multi-Agent orchestration และการเชื่อมต่อระบบภายนอกไว้ในแอปเดียว

เมนูหลักประกอบด้วย Home, AI Chat, Agent Center, Library, Knowledge Graph, GitHub, Google Workspace, Local API & Service, System Monitor และ Settings

ข้อมูลหลักของระบบถูกออกแบบให้เก็บในเครื่องเป็นหลัก และ Windows Service จะทำหน้าที่ดูแล Local API ที่พอร์ต 8787

---

# ส่วนที่ 1 — การติดตั้งบน Windows

## 2. ความต้องการของระบบ

แนะนำให้ใช้ Windows 10 หรือ Windows 11 แบบ 64-bit, มีสิทธิ์ Administrator สำหรับการติดตั้ง Windows Service และมีพื้นที่ว่างอย่างน้อยประมาณ 500 MB ขึ้นไป

การเชื่อมต่ออินเทอร์เน็ตจำเป็นเฉพาะฟังก์ชันที่ต้องใช้บริการภายนอก เช่น GitHub, Google Workspace หรือ AI provider

ตัว installer มี Python runtime และ ServiceHost ที่จำเป็นรวมมาด้วย ดังนั้นผู้ใช้ทั่วไปไม่จำเป็นต้องติดตั้ง Python หรือ .NET SDK แยก

## 3. ไฟล์ติดตั้ง

ไฟล์ติดตั้งถูกสร้างในรูปแบบ:

```text
Research-OS-Setup-<version>-x64.exe
```

สำหรับ build ปัจจุบัน ให้เลือก installer ที่มาจาก Research OS Release pipeline และผ่าน Installer Validation แล้ว

### หมายเหตุเรื่องเลขเวอร์ชัน installer

ขณะจัดทำเอกสารนี้ metadata ภายใน Inno Setup ยังมีค่า `0.6.0` แม้ตัวแอปกำลัง promote เป็น Research OS `1.0.0` ดังนั้นชื่อไฟล์ installer บาง build อาจยังแสดง `Research-OS-Setup-0.6.0-x64.exe` จนกว่าจะ sync packaging metadata ให้ตรงกับ app version

## 4. ขั้นตอนติดตั้ง

1. ดาวน์โหลดไฟล์ `Research-OS-Setup-*-x64.exe`
2. ดับเบิลคลิกไฟล์ติดตั้ง
3. เมื่อ Windows ขอสิทธิ์ Administrator ให้เลือก **Yes**
4. เลือกตำแหน่งติดตั้ง หรือใช้ค่ามาตรฐาน `C:\Program Files\Research OS`
5. เลือกว่าจะสร้าง Desktop shortcut หรือไม่
6. เลือก **Install**
7. Installer จะคัดลอกแอป, Local API, ServiceHost และ Python runtime ลงเครื่อง
8. Installer จะติดตั้ง Windows Service ชื่อ `ResearchOSService`
9. เมื่อเสร็จสามารถเลือก **Launch Research OS after installation** เพื่อเปิดแอปทันที

## 5. สิ่งที่ installer สร้างให้

ตัวโปรแกรมอยู่ที่:

```text
C:\Program Files\Research OS
```

โครงสร้างหลักประกอบด้วย:

```text
app\
tools\research_os_service\publish\
tools\research_os_api\
tools\research_curator\
runtime\python\
scripts\
```

ข้อมูลผู้ใช้และข้อมูลระบบอยู่ที่:

```text
C:\ProgramData\ResearchOS
```

โฟลเดอร์สำคัญ:

```text
C:\ProgramData\ResearchOS\database
C:\ProgramData\ResearchOS\sessions
C:\ProgramData\ResearchOS\artifacts
C:\ProgramData\ResearchOS\backups
C:\ProgramData\ResearchOS\logs
```

ข้อมูลใน `ProgramData\ResearchOS` ถูกแยกจากตัวโปรแกรม เพื่อให้การอัปเดตหรือถอนโปรแกรมไม่ลบ Memory, sessions และ backups โดยอัตโนมัติ

---

# ส่วนที่ 2 — ตรวจสอบหลังติดตั้ง

## 6. ตรวจ Windows Service

เปิด PowerShell แบบ **Run as Administrator** แล้วใช้:

```powershell
Get-Service ResearchOSService
```

สถานะปกติควรเป็น `Running`

หรือใช้สคริปต์ของ Research OS:

```powershell
& "C:\Program Files\Research OS\scripts\research-os-service.ps1" -Action status -DataDir "C:\ProgramData\ResearchOS"
```

ระบบจะแสดงข้อมูลคล้าย:

```text
Research OS Service: Running
Service name       : ResearchOSService
Local API          : http://127.0.0.1:8787
```

## 7. ตรวจ Local API

เปิด Browser แล้วเข้า:

```text
http://127.0.0.1:8787/health
```

หรือใช้ PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8787/health
```

ตรวจ provider endpoint:

```powershell
Invoke-RestMethod http://127.0.0.1:8787/v1/providers
```

---

# ส่วนที่ 3 — การเปิดและใช้งานแอป

## 8. เปิด Research OS

เปิดได้จาก Desktop shortcut, Start Menu หรือไฟล์โดยตรง:

```text
C:\Program Files\Research OS\app\research_os_flutter.exe
```

เมื่อเปิดแอป ระบบ UI จะเชื่อมต่อ Local API เพื่ออ่านสถานะ Memory, Agents, Knowledge และ service ต่าง ๆ

---

# ส่วนที่ 4 — วิธีใช้เมนูหลัก

## 9. Home

ใช้เป็น Dashboard หลักสำหรับดูภาพรวม Research OS และสถานะบริการสำคัญ แนะนำให้เริ่มจากหน้านี้หลังเปิดโปรแกรม

## 10. AI Chat

ใช้สำหรับสนทนากับ AI ผ่าน provider ที่ระบบกำหนด

ขั้นตอนพื้นฐาน:

1. เปิด **AI Chat**
2. พิมพ์คำถามหรืองานที่ต้องการ
3. ส่งข้อความ
4. ตรวจผลลัพธ์ก่อนนำไปใช้งานจริง

ถ้า Chat เชื่อม provider ไม่ได้ ให้ตรวจ **Settings**, **System Monitor** และ `/v1/providers`

## 11. Agent Center

Agent Center เป็นศูนย์ควบคุม Multi-Agent ของ Research OS

Agent ที่ลงทะเบียนใน V1 ได้แก่ Research Agent, Document Agent, GitHub Agent, Google Workspace Agent และ Shift Agent

หน้า Agent Center แสดง Runtime overview ได้แก่ Router, Task Queue, Event Bus และ Shared Context

### สร้าง Multi-Agent orchestration

1. เปิด **Agent Center**
2. ไปที่ **Multi-Agent orchestration**
3. กด **Create orchestration**
4. กำหนด Objective ของงาน
5. เพิ่ม Steps ที่ต้องทำ
6. กำหนด dependency ระหว่าง step หากจำเป็น
7. สร้าง orchestration
8. ตรวจ orchestration card ที่แสดงสถานะของ run
9. กด Execute เมื่อพร้อมให้ระบบเริ่มทำงาน

### Confirmation Gate

งานที่มีสิทธิ์เขียนหรือเปลี่ยนข้อมูลอาจถูกหยุดรอ confirmation

เมื่อเห็นสถานะรออนุมัติ ให้ตรวจ objective และผลของ step ให้ครบ แล้วกด Confirm เฉพาะเมื่อยอมรับการเปลี่ยนแปลง

หลักการของ V1 คือ read action สามารถทำงานได้ตาม permission ส่วน write-capable action ต้องผ่าน confirmation policy ตามที่กำหนด

## 12. Library

ใช้สำหรับดูและจัดการ Research Artifacts และข้อมูลความรู้ที่ Research OS เก็บไว้

## 13. Knowledge Graph

ใช้ดูความสัมพันธ์ระหว่าง Knowledge nodes, artifacts และข้อมูลที่เชื่อมโยงกัน

## 14. GitHub

ใช้สำหรับพื้นที่ทำงานที่เกี่ยวข้องกับ GitHub เช่น Repository, Commit, Pull Request, Issues และ Workflows ตามสิทธิ์ที่ระบบเชื่อมต่อไว้

สำหรับการเปลี่ยนแปลงที่มีผลต่อ repository ควรตรวจรายละเอียดทุกครั้งก่อนยืนยัน write action

## 15. Google Workspace

ใช้สำหรับงานที่เกี่ยวข้องกับ Drive, Docs, Sheets, Calendar, Gmail และ Workspace เมื่อมีการเชื่อมต่อและให้สิทธิ์ไว้แล้ว

งานเขียนข้อมูลควรผ่าน confirmation ตามนโยบายของระบบ

## 16. Local API & Service

ใช้สำหรับตรวจหรือควบคุม Local API และ Windows Service

Local API มาตรฐาน:

```text
http://127.0.0.1:8787
```

หากแอปแสดงว่า API unavailable ให้ตรวจหน้านี้ก่อน

## 17. System Monitor

ใช้ดูสุขภาพระบบและ component สำคัญ เช่น Local API, backend และ service ต่าง ๆ

## 18. Settings

ใช้ตั้งค่า Theme, API Base URL และการตั้งค่าที่ UI รองรับ

สำหรับการติดตั้ง local แบบมาตรฐาน API Base URL ควรชี้ไปที่:

```text
http://127.0.0.1:8787
```

---

# ส่วนที่ 5 — การใช้งาน Local API โดยตรง

## 19. Health

```http
GET /health
```

```powershell
Invoke-RestMethod http://127.0.0.1:8787/health
```

## 20. Providers

```http
GET /v1/providers
```

```powershell
Invoke-RestMethod http://127.0.0.1:8787/v1/providers
```

## 21. Multi-Agent orchestration API

```http
GET /v1/agents/orchestrations
POST /v1/agents/orchestrations
GET /v1/agents/orchestrations/{run_id}
POST /v1/agents/orchestrations/{run_id}/execute
POST /v1/agents/orchestrations/{run_id}/confirm
```

---

# ส่วนที่ 6 — การควบคุม Windows Service

คำสั่งต่อไปนี้ควรเปิด PowerShell แบบ Administrator

## 22. ดูสถานะ

```powershell
& "C:\Program Files\Research OS\scripts\research-os-service.ps1" -Action status -DataDir "C:\ProgramData\ResearchOS"
```

## 23. Start

```powershell
& "C:\Program Files\Research OS\scripts\research-os-service.ps1" -Action start -DataDir "C:\ProgramData\ResearchOS"
```

## 24. Stop

```powershell
& "C:\Program Files\Research OS\scripts\research-os-service.ps1" -Action stop -DataDir "C:\ProgramData\ResearchOS"
```

## 25. Restart

```powershell
& "C:\Program Files\Research OS\scripts\research-os-service.ps1" -Action restart -DataDir "C:\ProgramData\ResearchOS"
```

ระบบถูกตั้งให้ Service เริ่มแบบ delayed-auto และมี recovery restart เมื่อ service ล้ม

---

# ส่วนที่ 7 — การอัปเดต

## 26. ก่อนอัปเดต

แนะนำให้ปิด Research OS UI, ตรวจ `C:\ProgramData\ResearchOS\backups`, ใช้ installer ที่ผ่าน Release/Installer Validation และตรวจ version กับ SHA/digest ของ release หากมี manifest แนบมา

เนื่องจาก user data แยกอยู่ใน `ProgramData\ResearchOS` การติดตั้งเวอร์ชันใหม่ควรไม่ลบข้อมูล local เดิม

---

# ส่วนที่ 8 — การถอนการติดตั้ง

## 27. ถอนจาก Windows

ไปที่:

```text
Settings > Apps > Installed apps > Research OS > Uninstall
```

ระหว่างถอนการติดตั้ง ระบบจะเรียกสคริปต์เพื่อลบ `ResearchOSService`

หลังถอนโปรแกรม ข้อมูลใน:

```text
C:\ProgramData\ResearchOS
```

จะถูกเก็บไว้ เพื่อรักษา Local Memory, sessions, artifacts และ backups

หากต้องการล้างข้อมูลทั้งหมดจริง ๆ ควรสำรองข้อมูลที่ต้องการเก็บก่อน แล้วจึงลบ `C:\ProgramData\ResearchOS` ด้วยตนเอง

---

# ส่วนที่ 9 — แก้ปัญหาเบื้องต้น

## 28. เปิดแอปได้ แต่ Agent Center ขึ้น API unavailable

ตรวจ:

```powershell
Get-Service ResearchOSService
Invoke-RestMethod http://127.0.0.1:8787/health
```

หาก service ไม่ Running ให้ restart:

```powershell
& "C:\Program Files\Research OS\scripts\research-os-service.ps1" -Action restart -DataDir "C:\ProgramData\ResearchOS"
```

## 29. พอร์ต 8787 ใช้งานไม่ได้

ตรวจ listener:

```powershell
Get-NetTCPConnection -LocalPort 8787 -State Listen
```

Research OS service script ถูกออกแบบให้ตรวจและหยุดเฉพาะ process ที่ยืนยันได้ว่าเป็น Research OS API โดยไม่ปิด process อื่นแบบสุ่ม

## 30. หา log

ตรวจที่:

```text
C:\ProgramData\ResearchOS\logs
```

## 31. Windows Service หาย

เปิด PowerShell แบบ Administrator แล้วติดตั้ง service ใหม่:

```powershell
& "C:\Program Files\Research OS\scripts\research-os-service.ps1" -Action install -DataDir "C:\ProgramData\ResearchOS"
```

## 32. AI provider ใช้งานไม่ได้

ตรวจตามลำดับ: Local API `/health`, `/v1/providers`, Settings/provider configuration, การเชื่อมต่ออินเทอร์เน็ต และ System Monitor

อย่าลบ Memory หรือ ProgramData เพียงเพราะ provider ภายนอกเชื่อมต่อไม่ได้

---

# ส่วนที่ 10 — Quick Start

สำหรับผู้ใช้ทั่วไป หลังติดตั้งให้ทำตามลำดับนี้:

```text
1. เปิด Research OS
2. ตรวจ Home / System Monitor
3. ตรวจว่า Local API พร้อม
4. เข้า AI Chat สำหรับงานทั่วไป
5. เข้า Agent Center สำหรับงาน Multi-Agent
6. กด Create orchestration
7. ระบุ Objective และ Steps
8. Execute
9. ตรวจผล
10. Confirm เฉพาะ write action ที่ต้องการจริง
```

---

# สรุป

Research OS V1 ถูกออกแบบให้ผู้ใช้ทั่วไปติดตั้งผ่าน Setup EXE เพียงครั้งเดียว ตัว installer จะจัดเตรียม Desktop app, bundled Python runtime, Local API และ Windows Service ให้โดยอัตโนมัติ ส่วนข้อมูลสำคัญถูกเก็บแยกไว้ใน `C:\ProgramData\ResearchOS` เพื่อรองรับการอัปเดต การกู้คืน และ rollback ในอนาคต

สำหรับการใช้งานประจำวัน ให้เริ่มจาก Home/AI Chat และใช้ Agent Center เมื่อต้องการงานหลาย Agent หรือ workflow ที่มี dependency และ confirmation gate
